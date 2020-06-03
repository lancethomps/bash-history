#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import logging
from typing import List, Tuple

from bashhistory.configs import BashHistoryBaseArgs, BashHistoryColorArgs, BashHistoryConfig, BashHistorySelectArgs, get_or_load_config, InsertScriptArgs, SelectScriptArgs
from bashhistory.utils import try_import_argcomplete
from ltpylib.opts import PagerArgs, parse_args_and_init_others, RegexCasingArgs


def hist():
  try:
    _query_db_and_output(with_pattern_positional=False)
  except KeyboardInterrupt:
    exit(130)


def hist_db_create():
  try:
    from bashhistory.db_commands import create_db

    _parse_db_create_args()
    create_db()
  except KeyboardInterrupt:
    exit(130)


def hist_db_insert():
  try:
    from bashhistory.parser import parse_history
    from bashhistory.parser import should_skip_command
    from bashhistory.db_commands import insert_command

    args = _parse_insert_args()

    sequence, command = parse_history(args.command)

    if sequence is None or command is None:
      print("Could not parse command output")
      exit(1)

    if should_skip_command(command, verbose=args.verbose):
      exit(0)

    insert_command(
      command,
      exit_code=args.exit_code,
      pid=args.pid,
      sequence=sequence,
    )
  except KeyboardInterrupt:
    exit(130)


def hist_grep():
  try:
    _query_db_and_output(with_pattern_positional=True)
  except KeyboardInterrupt:
    exit(130)


def hist_grep_copy():
  try:
    from ltpylib import macos

    selected_commands = _query_db_and_select_commands()
    print("\n".join(selected_commands))
    macos.pbcopy("\n".join(selected_commands))
    logging.info("Copied!")
  except KeyboardInterrupt:
    exit(130)


def hist_grep_exec():
  try:
    from ltpylib import logs
    from ltpylib import procs

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
  from bashhistory.output import ask_user_to_select_command, create_results_output
  from bashhistory.query_runner import query_db

  config, args = _get_config_and_select_args()
  results, column_max_lengths = query_db(args, config=config, use_command_line=True)

  if not results:
    exit(1)

  output_lines = create_results_output(config, args, results, column_max_lengths)
  return ask_user_to_select_command(results, output_lines)


def _query_db_and_output(with_pattern_positional: bool = True):
  from bashhistory.output import ask_user_to_select_command, create_results_output
  from bashhistory.query_runner import query_db

  config, args = _get_config_and_select_args(with_pattern_positional=with_pattern_positional)

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


def _get_config_and_select_args(with_pattern_positional: bool = True) -> Tuple[BashHistoryConfig, SelectScriptArgs]:
  config = get_or_load_config()
  args = _parse_select_args(config, with_pattern_positional)
  return config, args


def _create_arg_parser() -> argparse.ArgumentParser:
  arg_parser = argparse.ArgumentParser()
  BashHistoryBaseArgs.add_arguments_to_parser(arg_parser)
  return arg_parser


def _parse_db_create_args() -> BashHistoryBaseArgs:
  arg_parser = _create_arg_parser()
  try_import_argcomplete(arg_parser)
  return InsertScriptArgs(parse_args_and_init_others(arg_parser))


def _parse_insert_args() -> InsertScriptArgs:
  arg_parser = _create_arg_parser()

  arg_parser.add_argument("--exit-code", "-e", help="set to $?", default=0, type=int)
  arg_parser.add_argument("--command", "-c", help="set to $(HISTTIMEFORMAT= history 1)", default="")
  arg_parser.add_argument("--pid", "-p", help="set to $$", default=0, type=int)

  try_import_argcomplete(arg_parser)
  return InsertScriptArgs(parse_args_and_init_others(arg_parser))


def _parse_select_args(config: BashHistoryConfig, with_pattern_positional: bool) -> SelectScriptArgs:
  arg_parser = _create_arg_parser()

  BashHistoryColorArgs.add_arguments_to_parser(arg_parser)
  PagerArgs.add_arguments_to_parser(arg_parser, default_pager=config.pager)
  RegexCasingArgs.add_arguments_to_parser(arg_parser)
  BashHistorySelectArgs.add_arguments_to_parser(arg_parser, config, with_pattern_positional=with_pattern_positional)

  try_import_argcomplete(arg_parser)
  return SelectScriptArgs(parse_args_and_init_others(arg_parser))
