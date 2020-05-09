#!/usr/bin/env python
import argparse
import configparser
import os
from typing import List, Union


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
    self.pattern: str = args.pattern

  @staticmethod
  def add_arguments_to_parser(arg_parser: argparse.ArgumentParser, config: BashHistoryConfig) -> argparse.ArgumentParser:
    arg_parser.add_argument("--columns", default=config.columns)
    arg_parser.add_argument("--limit", type=int, default=config.limit)
    arg_parser.add_argument("--limit-order", default=config.limit_order)
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
