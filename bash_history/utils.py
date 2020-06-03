#!/usr/bin/env python
import logging
from typing import List


class Term:
  HEADER = '\033[95m'
  BLUE = '\033[94m'
  GREEN = '\033[92m'
  YELLOW = '\033[93m'
  RED = '\033[91m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'
  ENDC = '\033[0m'


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


def log_sql_callback(query: str):
  logging.debug(query)


def try_import_argcomplete(arg_parser):
  try:
    import argcomplete

    argcomplete.autocomplete(arg_parser)
  except ImportError:
    pass
