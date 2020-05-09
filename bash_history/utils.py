#!/usr/bin/env python


class Term:
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'


def try_import_argcomplete(arg_parser):
  try:
    import argcomplete

    argcomplete.autocomplete(arg_parser)
  except ImportError:
    pass
