#!/usr/bin/env python
import argparse
import configparser
import os
from getpass import getuser
from pathlib import Path
from typing import Dict, List, Union

from bash_history.utils import Term


class BashHistoryConfig(object):

  def __init__(self, config_file):
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str

    if config_file and os.path.isfile(config_file):
      with open(config_file, "r") as fr:
        config_file_contents = fr.read()

      if '[DEFAULT]' not in config_file_contents:
        config_file_contents = "[DEFAULT]\n" + config_file_contents

      config.read_string(config_file_contents)

    self.config_file = config_file
    defaults = config.defaults()

    self.columns = defaults.get("columns", "at,command")
    self.limit = int(defaults.get("limit", os.getenv("BASH_HIST_SELECT_LIMIT", "50")))
    self.limit_order = defaults.get("limit_order", "at DESC")
    self.pager = defaults.get("pager") if "pager" in defaults else os.getenv("BASH_HIST_PAGER", os.getenv("PAGER"))
    self.sqlite_regexp_loader = defaults.get("sqlite_regexp_loader")

    self.column_colors: Dict[str, str] = {
      "at": Term.YELLOW,
    }
    if "column_colors" in defaults:
      for mapping in defaults.get("column_colors").split(","):
        column, color_name = mapping.split("=")

        if color_name.upper() == "NONE":
          self.column_colors.pop(column)
          continue

        if not hasattr(Term, color_name.upper()):
          raise ValueError("column_colors config using invalid color: %s" % mapping)

        self.column_colors[column] = getattr(Term, color_name.upper())


class BashHistoryColorArgs(object):

  def __init__(self, args: argparse.Namespace):
    self.no_color: bool = args.no_color
    self.use_color: bool = args.use_color

  def should_use_color(self, default: bool = True) -> bool:
    if self.use_color:
      return True

    if self.no_color:
      return False

    return default

  @staticmethod
  def add_arguments_to_parser(arg_parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    arg_parser.add_argument('--no-color', action="store_true")
    arg_parser.add_argument('--use-color', action="store_true")
    return arg_parser


class BashHistoryPagerArgs(object):

  def __init__(self, args: argparse.Namespace):
    self.no_pager: bool = args.no_pager
    self.pager: str = args.pager
    self.use_pager: bool = args.use_pager

  def should_use_pager(self, default: bool = True) -> bool:
    if self.use_pager:
      return True

    if self.no_pager:
      return False

    return default

  @staticmethod
  def add_arguments_to_parser(arg_parser: argparse.ArgumentParser, config: BashHistoryConfig) -> argparse.ArgumentParser:
    arg_parser.add_argument('--no-pager', action="store_true")
    arg_parser.add_argument('--pager', default=config.pager)
    arg_parser.add_argument('--use-pager', action="store_true")
    return arg_parser


class BashHistorySelectArgs(object):

  def __init__(self, args: argparse.Namespace):
    self.columns: List[str] = args.columns.split(",")
    self.limit: int = args.limit
    self.limit_order = args.limit_order
    self.unique: bool = args.unique

    self.dir: List[str] = args.dir if args.dir else []
    self.dir_regex: str = args.dir_regex
    self.exit_code: List[int] = args.exit_code if args.exit_code else []
    self.host: List[str] = args.host if args.host else []
    self.host_regex: str = args.host_regex
    self.user: List[str] = args.user if args.user else []

    self.me: bool = args.me
    self.pwd: bool = args.pwd
    self.root: bool = args.root

    if self.me:
      self.user.append(getuser())

    if self.pwd:
      self.dir.append(os.getcwd())

    if self.root:
      self.user.append("root")

    self.pattern: str = args.pattern if "pattern" in args else None
    self.pattern_exact: bool = args.pattern_exact if "pattern_exact" in args else False
    self.pattern_sql: bool = args.pattern_sql if "pattern_sql" in args else False

    if self.dir:
      self.dir = [Path(filter_dir).as_posix() for filter_dir in self.dir]

  @staticmethod
  def add_arguments_to_parser(arg_parser: argparse.ArgumentParser, config: BashHistoryConfig, with_pattern_positional: bool = True) -> argparse.ArgumentParser:
    arg_parser.add_argument("--columns", "-c", default=config.columns)
    arg_parser.add_argument("--limit", "-l", type=int, default=config.limit)
    arg_parser.add_argument("--limit-order", default=config.limit_order)
    arg_parser.add_argument("--unique", "-u", action="store_true")
    
    arg_parser.add_argument("--dir", "-d", action="append")
    arg_parser.add_argument("--dir-regex", "-dr")
    arg_parser.add_argument("--exit-code", action="append", type=int)
    arg_parser.add_argument("--host", action="append")
    arg_parser.add_argument("--host-regex", "-hr")
    arg_parser.add_argument("--user", action="append")

    arg_parser.add_argument("--me", action="store_true")
    arg_parser.add_argument("--pwd", "-p", action="store_true")
    arg_parser.add_argument("--root", action="store_true")

    if with_pattern_positional:
      arg_parser.add_argument("--pattern-exact", "-exact", action="store_true")
      arg_parser.add_argument("--pattern-sql", "-sql", action="store_true")
      arg_parser.add_argument('pattern')
      
    return arg_parser


LOADED_CONFIG: Union[BashHistoryConfig, None] = None


def get_or_load_config():
  global LOADED_CONFIG
  if LOADED_CONFIG is None:
    LOADED_CONFIG = BashHistoryConfig(get_config_file())

  return LOADED_CONFIG


def get_config_file():
  return os.getenv("BASH_HISTORY_CONFIG", os.path.expanduser("~/.config/bash-history/bash-history.conf"))
