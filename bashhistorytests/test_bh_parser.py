#!/usr/bin/env python
from typing import Tuple, Union

import pytest

from bashhistory import bh_parser


@pytest.mark.parametrize("history,expected", [
  (" 2477  make init", ("2477", "make init")),
])
def test_parse_history(history: str, expected: Tuple[Union[str, None], Union[str, None]]):
  assert expected == bh_parser.parse_history(history)


@pytest.mark.parametrize("command,expected", [
  ("make init", False),
  (" echo this should be skipped", True),
])
def test_should_skip_command(command: str, expected: bool):
  assert expected == bh_parser.should_skip_command(command)
