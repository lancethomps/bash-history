#!/usr/bin/env python
from typing import List, Tuple, Union

from bashhistory.bh_configs import SelectScriptArgs

OP_REGEXP = "REGEXP"
SELF_COMMANDS = [
  "hg",
  "hgc",
  "hge",
  "hgp",
  "hgu",
  "hist",
  "hist_db_create",
  "hist_db_insert",
  "hist_grep",
  "hist_grep_copy",
  "hist_grep_exec",
]


def add_filter_if_valid(
  filters: List[str],
  params: List,
  field: str,
  maybe_add: Union[List, str, int],
  sql_operator: str = "=",
):
  if maybe_add:
    if isinstance(maybe_add, list) and len(maybe_add) == 1:
      maybe_add = maybe_add[0]

    if isinstance(maybe_add, list):
      filters.append("%s IN (%s)" % (field, ", ".join("?" * len(maybe_add))))
      params.extend(maybe_add)
    else:
      filters.append("%s %s ?" % (field, sql_operator))
      params.append(maybe_add)


def create_sql(query: str, params: list) -> str:
  if not params:
    return query

  parsed_query_parts = []
  query_parts = query.split("?")
  for index, param in enumerate(params):
    query_part = query_parts[index]
    parsed_query_parts.append(query_part)

    if isinstance(param, str):
      param_str = "'%s'" % (param.replace("'", "''"))
    elif isinstance(param, bool):
      param_str = "TRUE" if param else "FALSE"
    else:
      param_str = str(param)

    parsed_query_parts.append(param_str)

  parsed_query_parts.append(query_parts[-1])

  return "".join(parsed_query_parts)


def query_builder(args: SelectScriptArgs, use_command_line: bool = False) -> Tuple[str, list]:
  params = []

  filters = ["1"]

  add_filter_if_valid(filters, params, "DATE(at)", args.at)
  add_filter_if_valid(filters, params, "DATETIME(at)", args.at_datetime)
  add_filter_if_valid(filters, params, "at", args.at_from, sql_operator=">=")
  add_filter_if_valid(filters, params, "at", args.at_to, sql_operator="<=")
  add_filter_if_valid(filters, params, "exit_code", args.exit_code)
  add_filter_if_valid(filters, params, "host", args.host, sql_operator="LIKE")
  add_filter_if_valid(filters, params, "host", args.host_regex, sql_operator=OP_REGEXP)
  add_filter_if_valid(filters, params, "pwd", args.dir)
  add_filter_if_valid(filters, params, "pwd", args.dir_regex, sql_operator=OP_REGEXP)
  add_filter_if_valid(filters, params, "user", args.user)

  if args.raw_sql_filter:
    filters.extend(args.raw_sql_filter)

  if not args.return_self:
    add_filter_if_valid(filters, params, "command", "^(%s)($| )" % "|".join(SELF_COMMANDS), sql_operator=("NOT " + OP_REGEXP))

  if args.pattern:
    pattern = args.pattern
    ignore_case = args.should_ignore_case(pattern)
    pattern_type = OP_REGEXP
    if args.pattern_exact:
      pattern_type = "="
    elif args.pattern_sql:
      if ignore_case:
        pattern_type = "ILIKE"
      else:
        pattern_type = "LIKE"
    elif ignore_case:
      pattern = "(?i)" + pattern

    add_filter_if_valid(filters, params, "command", pattern, pattern_type)

  if use_command_line:
    field_and_columns = []
    for col in args.columns:
      field_and_columns.append("'%s'" % col)
      field_and_columns.append(col)
    select_columns = "JSON_OBJECT(%s)" % ", ".join(field_and_columns)
  else:
    select_columns = ", ".join(args.columns)

  sql = """
SELECT
  %s
FROM commands
WHERE
  %s
ORDER BY
  %s
LIMIT ?
  """ % (
    select_columns,
    "\n  AND ".join(filters),
    args.limit_order,
  )
  params.append(args.limit)
  return sql, params
