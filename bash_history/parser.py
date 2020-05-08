#!/usr/bin/env python
import re
from typing import Tuple, Union


def parse_history(history) -> Tuple[Union[str, None], Union[str, None]]:
  match = re.search(r"^\s+(\d+) {2}(.*)$", history, re.MULTILINE and re.DOTALL)
  if match:
    return match.group(1), match.group(2)
  else:
    return None, None


def should_skip_command(command: str, verbose: bool = False) -> bool:
  if command.startswith(" "):
    if verbose:
      print("Skipping command starting with space: `%s`" % command)

    return True

  return False
