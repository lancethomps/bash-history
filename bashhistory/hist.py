#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import logging
from typing import List, Tuple

from bashhistory.configs import BashHistoryColorArgs, BashHistoryConfig, BashHistoryPagerArgs, BashHistorySelectArgs, get_or_load_config
from bashhistory.output import ask_user_to_select_command, create_results_output
from bashhistory.query_runner import query_db
from bashhistory.utils import try_import_argcomplete
from ltpylib import logs, macos, opts, procs


class SelectScriptArgs(BashHistoryColorArgs, BashHistoryPagerArgs, BashHistorySelectArgs):

  def __init__(self, args: argparse.Namespace):
    BashHistoryColorArgs.__init__(self, args)
    BashHistoryPagerArgs.__init__(self, args)

    BashHistorySelectArgs.__init__(self, args)

    self.verbose: bool = args.verbose


def hist():
  try:
    _query_db_and_output(with_pattern_positional=False)
  except KeyboardInterrupt:
    exit(130)


def hist_grep():
  try:
    _query_db_and_output(with_pattern_positional=True)
  except KeyboardInterrupt:
    exit(130)


def hist_grep_copy():
  try:
    selected_commands = _query_db_and_select_commands()
    print("\n".join(selected_commands))
    macos.pbcopy("\n".join(selected_commands))
    logging.info("Copied!")
  except KeyboardInterrupt:
    exit(130)


def hist_grep_exec():
  try:
    selected_commands = _query_db_and_select_commands()
    exit_code = 0
    for command in selected_commands:
      logging.warning("Running: %s\n%s", command, logs.LOG_SEP)
      result = procs.run_with_regular_stdout(
        ["bash", "-c", command],
        check=False,
      )
      if result.returncode != 0:
        exit_code = result.returncode

    exit(exit_code)
  except KeyboardInterrupt:
    exit(130)


def _query_db_and_select_commands() -> List[str]:
  config, args = _get_config_and_args()

  results, column_max_lengths = query_db(args, config=config, use_command_line=True)

  if not results:
    exit(1)

  output_lines = create_results_output(config, args, results, column_max_lengths)
  return ask_user_to_select_command(results, output_lines)


def _query_db_and_output(with_pattern_positional: bool = True):
  config, args = _get_config_and_args(with_pattern_positional=with_pattern_positional)

  if not with_pattern_positional:
    args.pattern = None

  results, column_max_lengths = query_db(args, config=config, use_command_line=True)

  if not results:
    exit(1)

  output_lines = create_results_output(config, args, results, column_max_lengths)

  if args.no_pager:
    print("\n".join(output_lines))
  else:
    selected_commands = ask_user_to_select_command(results, output_lines)
    print("\n".join(selected_commands))


def _get_config_and_args(with_pattern_positional: bool = True) -> Tuple[BashHistoryConfig, SelectScriptArgs]:
  config = get_or_load_config()
  args = _parse_select_args(config, with_pattern_positional)
  return config, args


def _parse_select_args(config: BashHistoryConfig, with_pattern_positional: bool) -> SelectScriptArgs:
  arg_parser = argparse.ArgumentParser()

  arg_parser.add_argument("-v", "--verbose", action="store_true")

  BashHistoryColorArgs.add_arguments_to_parser(arg_parser)
  BashHistoryPagerArgs.add_arguments_to_parser(arg_parser, config)

  BashHistorySelectArgs.add_arguments_to_parser(arg_parser, config, with_pattern_positional=with_pattern_positional)

  try_import_argcomplete(arg_parser)
  return SelectScriptArgs(opts.parse_args_and_init_others(arg_parser))
