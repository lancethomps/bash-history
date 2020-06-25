#!/usr/bin/env python
import logging
import shutil
from pathlib import Path


def can_use_sqlite_command_line(sqlite_regexp_loader: str) -> bool:
  if shutil.which("sqlite3") is None:
    logging.debug("CANNOT USE SQLITE COMMAND LINE. Could not find sqlite3 executable.")
    return False

  if not sqlite_regexp_loader:
    logging.debug("CANNOT USE SQLITE COMMAND LINE. No sqlite_regexp_loader config file supplied.")
    return False

  if not Path(sqlite_regexp_loader).exists() or not Path(sqlite_regexp_loader).is_file():
    logging.debug("CANNOT USE SQLITE COMMAND LINE. sqlite_regexp_loader config file not found: %s", sqlite_regexp_loader)
    return False

  return True


def log_sql_callback(query: str):
  logging.debug("SQL QUERY (Python)\n%s", query)


def try_import_argcomplete(arg_parser):
  try:
    import argcomplete

    argcomplete.autocomplete(arg_parser)
  except ImportError:
    pass
