#!/usr/bin/env python
import os
import sqlite3

from bash_history import db_commands


def connect(create_if_missing: bool = True) -> sqlite3.Connection:
  db_file = get_db_file()
  if create_if_missing and not os.path.exists(db_file):
    db_commands.create_db()

  return sqlite3.connect(db_file)


def close(db_conn: sqlite3.Connection, commit: bool = True):
  db_conn.commit()
  db_conn.close()


def get_db_file() -> str:
  return os.getenv("BASH_HIST_DB", os.path.expanduser("~/.bash_history.db"))
