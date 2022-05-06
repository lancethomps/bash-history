#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from bashhistory.bh_configs import BashHistoryBaseArgs, BashHistoryColorArgs, BashHistoryConfig, BashHistorySelectArgs, get_or_load_config, InsertScriptArgs, SelectScriptArgs
from bashhistory.bh_utils import try_import_argcomplete
from ltpylib.logs import log_with_title_sep
from ltpylib.opts import (
  create_default_arg_parser,
  log_args,
  PagerArgs,
  parse_args_and_init_others,
  RegexCasingArgs,
)


def hist():
  try:
    _query_db_and_output(with_pattern=False, default_args={"return_self": True})
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
    from bashhistory.bh_parser import parse_history
    from bashhistory.bh_parser import should_skip_command
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
    _query_db_and_output(with_pattern=True)
  except KeyboardInterrupt:
    exit(130)


def hist_grep_copy():
  try:
    from ltpylib import macos

    selected_commands = _query_db_and_select_commands(default_args={"unique": True})
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


def _query_db_and_select_commands(
  with_pattern: bool = True,
  require_pattern: bool = BashHistorySelectArgs.DEFAULT_REQUIRE_PATTERN,
  default_args: Dict[str, Any] = None,
) -> List[str]:
  from bashhistory.bh_output import ask_user_to_select_command, create_results_output
  from bashhistory.query_runner import query_db

  config, args = _get_config_and_select_args(with_pattern=with_pattern, require_pattern=require_pattern, default_args=default_args)
  results, column_max_lengths = query_db(args, config=config, use_command_line=True)

  if not results:
    exit(1)

  output_lines = create_results_output(config, args, results, column_max_lengths)
  return ask_user_to_select_command(results, output_lines)


def _query_db_and_output(
  with_pattern: bool = True,
  require_pattern: bool = BashHistorySelectArgs.DEFAULT_REQUIRE_PATTERN,
  default_args: Dict[str, Any] = None,
):
  from bashhistory.bh_output import ask_user_to_select_command, create_results_output
  from bashhistory.query_runner import query_db

  config, args = _get_config_and_select_args(with_pattern=with_pattern, require_pattern=require_pattern, default_args=default_args)

  if not with_pattern:
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


def _get_config_and_select_args(
  with_pattern: bool = True,
  require_pattern: bool = BashHistorySelectArgs.DEFAULT_REQUIRE_PATTERN,
  default_args: Dict[str, Any] = None,
) -> Tuple[BashHistoryConfig, SelectScriptArgs]:
  config = get_or_load_config()
  args = _parse_select_args(config, with_pattern, require_pattern)

  if default_args:
    for key, val in default_args.items():
      if hasattr(args, key) and getattr(args, key) is None:
        setattr(args, key, val)

  if args.verbose:
    log_with_title_sep("CONFIG", str(config.__dict__))
    log_args(args, include_raw_args=True)

  return config, args


def _create_arg_parser(with_pattern: bool) -> argparse.ArgumentParser:
  arg_parser = create_default_arg_parser()

  BashHistoryBaseArgs.add_arguments_to_parser(arg_parser)
  return arg_parser


def _parse_db_create_args() -> BashHistoryBaseArgs:
  arg_parser = _create_arg_parser(with_pattern=False)
  try_import_argcomplete(arg_parser)
  return InsertScriptArgs(parse_args_and_init_others(arg_parser))


def _parse_insert_args() -> InsertScriptArgs:
  arg_parser = _create_arg_parser(with_pattern=False)

  arg_parser.add_argument("--exit-code", "-e", help="set to $?", default=0, type=int)
  arg_parser.add_argument("--command", "-c", help="set to $(HISTTIMEFORMAT= history 1)", default="")
  arg_parser.add_argument("--pid", "-p", help="set to $$", default=0, type=int)

  try_import_argcomplete(arg_parser)
  return InsertScriptArgs(parse_args_and_init_others(arg_parser))


def _parse_select_args(config: BashHistoryConfig, with_pattern: bool, require_pattern: bool) -> SelectScriptArgs:
  arg_parser = _create_arg_parser(with_pattern=with_pattern)

  BashHistoryColorArgs.add_arguments_to_parser(arg_parser)
  PagerArgs.add_arguments_to_parser(arg_parser, default_pager=config.pager)
  RegexCasingArgs.add_arguments_to_parser(arg_parser)
  BashHistorySelectArgs.add_arguments_to_parser(arg_parser, config, with_pattern=with_pattern, require_pattern=require_pattern)

  try_import_argcomplete(arg_parser)

  parsed_args = parse_args_and_init_others(arg_parser)
  args = SelectScriptArgs(parsed_args)

  if args.pwd and config.other_home_paths:
    home_dir = Path.home()
    cwd = Path.cwd()
    if cwd == home_dir or cwd.is_relative_to(home_dir):
      cwd_rel = cwd.relative_to(home_dir)
      for home_path in config.other_home_paths:
        other_path = home_path.joinpath(cwd_rel).as_posix()
        if other_path not in args.dir:
          args.dir.append(other_path)

  return args
