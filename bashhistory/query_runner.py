#!/usr/bin/env python
import json
import logging
import sqlite3
from typing import Dict, List, Tuple

from bashhistory import db_connection
from bashhistory.bh_configs import BashHistoryConfig, get_or_load_config, SelectScriptArgs
from bashhistory.query_creator import create_sql, query_builder
from bashhistory.bh_utils import can_use_sqlite_command_line, log_sql_callback
from ltpylib import procs


def query_db(
  args: SelectScriptArgs,
  config: BashHistoryConfig = None,
  db_conn: sqlite3.Connection = None,
  use_command_line: bool = False,
) -> Tuple[List[dict], Dict[str, int]]:
  if not config:
    config = get_or_load_config()

  if use_command_line and not can_use_sqlite_command_line(config.sqlite_regexp_loader):
    logging.debug("Switching use_command_line to false.")
    use_command_line = False

  close_after = False
  query, params = query_builder(args, use_command_line=use_command_line)

  column_max_lengths = {}
  for column in args.columns:
    column_max_lengths[column] = len(column)

  if use_command_line:
    results: List[dict] = query_via_command_line(config, args, query, params)
  else:
    if not db_conn:
      close_after = True
      db_conn = db_connection.connect(load_regexp=True)
      db_conn.set_trace_callback(log_sql_callback)

    results: List[dict] = query_via_python(config, args, query, params, db_conn)

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


def query_via_command_line(config: BashHistoryConfig, args: SelectScriptArgs, query: str, params: List) -> List[dict]:
  results: List[dict] = []
  parsed_sql = create_sql(query, params)

  logging.debug("SQL QUERY (sqlite3 CLI)\n%s", parsed_sql)
  args.check_for_debug_and_exit()

  sqlite_cmd = [
    "sqlite3",
    "-cmd",
    ".load %s" % config.sqlite_regexp_loader,
    db_connection.get_db_file(),
    parsed_sql,
  ]
  command_result = procs.run(sqlite_cmd, check=True)
  for line in command_result.stdout.splitlines():
    results.append(json.loads(line))

  return results


def query_via_python(config: BashHistoryConfig, args: SelectScriptArgs, query: str, params: List, db_conn: sqlite3.Connection) -> List[dict]:
  results: List[dict] = []
  for row in db_conn.cursor().execute(query, params):
    row_dict = {}
    for idx in range(len(row)):
      column = args.columns[idx]
      val = row[idx]

      row_dict[column] = val

    results.append(row_dict)

  return results


def filter_for_unique_commands(results: List[dict]) -> List[dict]:
  filtered = []
  found_commands = []
  for result in results:
    command = result.get("command")
    if not command:
      filtered.append(result)
    elif command in found_commands:
      continue
    else:
      found_commands.append(command)
      filtered.append(result)

  return filtered
