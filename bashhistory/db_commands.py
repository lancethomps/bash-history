#!/usr/bin/env python
import json
import os
import sqlite3
from datetime import datetime
from getpass import getuser
from typing import Dict, List, Tuple

from bashhistory import db_connection
from bashhistory.configs import BashHistorySelectArgs
from bashhistory.query_creator import create_sql, query_builder
from bashhistory.utils import filter_for_unique_commands, log_sql_callback
from ltpylib import procs


class SQL:
  COLUMNS = [
    "command",
    "at",
    "host",
    "pwd",
    "user",
    "exit_code",
    "pid",
    "sequence",
  ]

  CREATE_COMMANDS: str = """
    DROP TABLE IF EXISTS commands
    ;

    CREATE TABLE commands (
      command   TEXT      NOT NULL,
      at        TIMESTAMP NOT NULL,
      host      TEXT      NOT NULL,
      pwd       TEXT      NOT NULL,
      user      TEXT      NOT NULL,
      exit_code INTEGER,
      pid       INTEGER,
      sequence  INTEGER
    )
    ;

    CREATE INDEX commands_at ON commands (at)
    ;

    CREATE INDEX commands_pwd ON commands (pwd)
    ;

    CREATE INDEX commands_exit_code ON commands (exit_code)
    ;
    """

  INSERT_COMMAND: str = """
    INSERT INTO commands(command, at, host, pwd, user, exit_code, pid, sequence)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """


def create_db():
  db_conn = db_connection.connect(create_if_missing=False)
  db_conn.executescript(SQL.CREATE_COMMANDS)
  db_conn.commit()
  db_conn.close()


def select_commands(
  args: BashHistorySelectArgs,
  db_conn: sqlite3.Connection = None,
  use_command_line: bool = False,
) -> Tuple[List[dict], Dict[str, int]]:
  close_after = False
  if not use_command_line and not db_conn:
    close_after = True
    db_conn = db_connection.connect(load_regexp=True)
    db_conn.set_trace_callback(log_sql_callback)

  results: List[dict] = []
  query, params = query_builder(args, use_command_line=use_command_line)

  column_max_lengths = {}
  for column in args.columns:
    column_max_lengths[column] = len(column)

  if use_command_line:
    command_result = procs.run([
      "sqlite3",
      db_connection.get_db_file(),
      create_sql(query, params),
    ], check=True)
    for line in command_result.stdout.splitlines():
      results.append(json.loads(line))
  else:
    for row in db_conn.cursor().execute(query, params):
      row_dict = {}
      for idx in range(len(row)):
        column = args.columns[idx]
        val = row[idx]

        row_dict[column] = val

      results.append(row_dict)

  if args.unique:
    results = filter_for_unique_commands(results)

  for row_dict in results:
    for column, val in row_dict.items():
      if val:
        val_length = len(str(val))
        if val_length > column_max_lengths.get(column):
          column_max_lengths[column] = val_length

  if close_after:
    db_connection.close(db_conn, commit=False)

  return results, column_max_lengths


def insert_command(
  command: str,
  at: datetime = None,
  host: str = None,
  pwd: str = None,
  user: str = None,
  exit_code: int = None,
  pid: int = None,
  sequence: int = None,
  db_conn: sqlite3.Connection = None,
  commit: bool = True,
):
  if not at:
    at = datetime.utcnow()

  if not host:
    host = os.uname()[1]

  if not pwd:
    pwd = os.getcwd()

  if not user:
    user = getuser()

  close_after = False
  if not db_conn:
    close_after = True
    db_conn = db_connection.connect()

  db_conn.execute(SQL.INSERT_COMMAND, [
    command,
    at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
    host,
    pwd,
    user,
    exit_code,
    pid,
    sequence,
  ])

  if close_after:
    db_connection.close(db_conn, commit=True)
  elif commit:
    db_conn.commit()
