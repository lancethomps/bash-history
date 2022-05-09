#!/usr/bin/env python
import os
import sqlite3

from bashhistory import db_commands


def connect(
  create_if_missing: bool = True,
  load_regexp: bool = False,
) -> sqlite3.Connection:
  db_file = get_db_file()
  if create_if_missing and not os.path.exists(db_file):
    db_commands.create_db()

  db_conn = sqlite3.connect(db_file, timeout=5.0)

  if load_regexp:
    load_regexp_function(db_conn)

  return db_conn


def close(db_conn: sqlite3.Connection, commit: bool = True):
  if commit:
    db_conn.commit()
  db_conn.close()


def get_db_file() -> str:
  return os.getenv("BASH_HIST_DB", os.path.expanduser("~/.bash_history.db"))


def load_regexp_function(db_conn):
  try:
    import pcre

    def sqlite_regexp(regex, item):
      return pcre.search(regex, item) is not None

    db_conn.create_function("REGEXP", 2, sqlite_regexp)
  except ImportError:
    import re

    def sqlite_regexp(regex, item):
      return re.search(regex, item) is not None

    db_conn.create_function("REGEXP", 2, sqlite_regexp)
