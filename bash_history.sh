#!/usr/bin/env bash
BASH_HIST_LOGS="${BASH_HIST_LOGS:-$HOME/.logs/bash_history}"
# shellcheck disable=SC2016
BASH_HIST_AWK_CMD='{printf "%s\t%s\t%s\n", substr($3,2), substr($1,1,19), $2}'
BASH_HIST_MAX_WIDTH="${BASH_HIST_MAX_WIDTH:-225}"

if test "${BASH_HIST_NO_WRITE:-}" = 'true'; then
  true
elif test -w "$HOME"; then
  if test -z "${ORIG_PROMPT_COMMAND:-}"; then
    export ORIG_PROMPT_COMMAND="${PROMPT_COMMAND:- }"
  else
    export PROMPT_COMMAND="$ORIG_PROMPT_COMMAND"
  fi
  log_tz_offset=$(python -c 'import time;import sys;sys.stdout.write(time.strftime("%z"))')
  _PWD_PREFIX=''
  if [ "$(id -u)" -eq 0 ]; then
    _PWD_PREFIX='root@'
  fi

  # shellcheck disable=SC2016
  log_cmd_pre='hist_db_insert --exit-code "$?" --pid "$$" --command "$(HISTTIMEFORMAT= history 1)"; _prev_cmd="$(fc -ln -0 2>/dev/null)"'
  log_cmd_post='unset _prev_cmd'
  # shellcheck disable=SC2016
  log_cmd='if [[ ${_prev_cmd} != "	  "* ]]; then echo "$(python -c "from datetime import datetime;import sys;sys.stdout.write(datetime.now().strftime(\"%Y-%m-%d %H:%M:%S.%f\")[:-3]);")'" $log_tz_offset"$'\t'"$_PWD_PREFIX"'$(pwd)${_prev_cmd}" >> '"$BASH_HIST_LOGS"'/bash-history_$(date "+%Y-%m-%d")_'$(hostname)'.log; fi'
  if test "$(id -u)" -ne 0; then
    ! test -d "$BASH_HIST_LOGS" && mkdir -p "$BASH_HIST_LOGS"
    export PROMPT_COMMAND="${log_cmd_pre}; ${log_cmd}; ${log_cmd_post}; ${PROMPT_COMMAND}"
  elif current_user=$(/bin/ls -l /dev/console | /usr/bin/awk '{ print $3 }'); then
    ! test -d "$BASH_HIST_LOGS" && sudo -u "$current_user" mkdir -p "$BASH_HIST_LOGS"
    export PROMPT_COMMAND="${log_cmd_pre}; ${log_cmd}; ${log_cmd_post}; ${PROMPT_COMMAND}"
  else
    echo "Running as root and current logged in user could not be determined, not writing history logs..."
  fi
  unset current_user log_cmd log_cmd_pre log_cmd_post log_tz_offset _PWD_PREFIX
else
  echo "It appears your home directory is read only, not writing history logs there..."
fi

function __pull_matches() {
  local ignore_commands
  ignore_commands="$1" && shift
  hist_grep "$@" | tail -n +2 | command grep -Ev '\s('"$ignore_commands"')(\s|$)' | sed '1!G;h;$!d' | head -"${BASH_HIST_SELECT_COUNT:-50}" | awk -F $'\t' "$BASH_HIST_AWK_CMD" | csvlook --tabs --no-header-row | tail -n +3
}
function __ask_user_to_select_cmd() {
  local found_cmd exit_val
  found_cmd="$(__pull_matches "$@" | fzf --no-sort --layout=reverse --multi --header='Please select the command from the list below.')"
  exit_val="$?"
  if test "$exit_val" -ne 0; then
    return "$exit_val"
  fi
  if test -z "$found_cmd"; then
    echo "Nothing selected, exiting..."
    return 1
  fi
  echo "$found_cmd"
}

function hist() {
  local use_pager=true
  local bh_pager="${BASH_HIST_PAGER:-$PAGER}"
  if test "${1-}" = '--no-pager'; then
    use_pager=false
    shift
  elif test "${1-}" = '--pager'; then
    use_pager=true
    shift
  elif test -z "${bh_pager}"; then
    use_pager=false
  elif ! test -t 1; then
    use_pager=false
  fi

  local size="${1-}"
  if test -z "$size"; then
    if test "$use_pager" = 'true'; then
      size='500'
    else
      size='50'
    fi
  fi
  local remaining_size="$size"
  local file_pos=1
  local curr_size=0
  local out add_out all_logs
  all_logs="$(ls -t "$BASH_HIST_LOGS/bash-history"*.log)"
  while ((size > curr_size)); do
    add_out="$(tail < "$(echo "$all_logs" | head "-$file_pos" | tail -1)" "-$remaining_size" | tail -r)"
    add_size="$(echo "$add_out" | wc -l | tr -d '\011\012\015')"
    file_pos="$((file_pos + 1))"
    curr_size="$((curr_size + add_size))"
    remaining_size="$((size - curr_size))"
    test -z "$out" && out="$add_out" || out="${out}"$'\n'"${add_out}"
  done
  if test "$use_pager" = 'true'; then
    {
      echo 'Command'$'\t''Time'$'\t''PWD'
      echo "$out" | awk -F $'\t' "$BASH_HIST_AWK_CMD"
    } | eval "${bh_pager}"
  else
    {
      echo 'Time'$'\t''PWD'$'\t''Command'
      echo "$out"
    }
  fi
}
function hist_grep() {
  local use_pager=true
  local bh_pager="${BASH_HIST_PAGER:-$PAGER}"
  if test "${1-}" = '--no-pager'; then
    use_pager=false
    shift
  elif test "${1-}" = '--pager'; then
    use_pager=true
    shift
  elif test -z "${bh_pager}"; then
    use_pager=false
  elif ! test -t 1; then
    use_pager=false
  fi
  local grep_args=("$@")
  if test "${1-}" = '--use-case'; then
    shift
    grep_args=("$@")
  elif ! [[ "${*: -1}" =~ [A-Z] ]]; then
    grep_args+=("-i")
  fi

  local old_nullglob all_log_files_temp all_log_files
  old_nullglob="$(shopt -p nullglob)"
  shopt -s nullglob
  all_log_files_temp=("$BASH_HIST_LOGS/bash-history"*.log)
  mapfile -td '' all_log_files < <(printf '%s\0' "${all_log_files_temp[@]}" | sort -rz)
  eval "$old_nullglob"

  if test "$use_pager" = 'true'; then
    {
      echo 'Command'$'\t''Time'$'\t''PWD'
      command grep --color=auto --no-filename -E "${grep_args[@]}" "${all_log_files[@]}" | sort -r | awk -F $'\t' "$BASH_HIST_AWK_CMD"
    } | eval "${bh_pager}"
  else
    {
      echo 'Time'$'\t''PWD'$'\t''Command'
      command grep --color=auto --no-filename -E "${grep_args[@]}" "${all_log_files[@]}" | sort
    }
  fi
}
function hist_grep_copy() {
  local exec_cmd_full exec_cmd exit_val
  exec_cmd_full="$(__ask_user_to_select_cmd 'hgc|hist_grep_copy' "$@")"
  exit_val="$?"
  if test "$exit_val" -ne 0; then
    return "$exit_val"
  fi
  echo "${exec_cmd_full}"
  exec_cmd="$(bash_history_extract_command "${exec_cmd_full}")"
  echo -n "$exec_cmd" | pbcopy
  exit_val=$?
  if [ $exit_val -eq 0 ]; then
    echo "Copied: $exec_cmd"
  fi
  return $exit_val
}
function hist_grep_exec() {
  local exec_cmd_full exec_cmd exit_val
  exec_cmd_full="$(__ask_user_to_select_cmd 'hge|hist_grep_exec' "$@")"
  exit_val="$?"
  if test "$exit_val" -ne 0; then
    return "$exit_val"
  fi
  echo "${exec_cmd_full}"
  exec_cmd="$(bash_history_extract_command "${exec_cmd_full}")"
  history -s "$exec_cmd"
  echo "Running: $exec_cmd"$'\n''---------------------------------'
  eval "$exec_cmd"
  return $?
}
function hist_grep_pwd() {
  local search
  search="$(pwd)\s.*${1}" && shift
  hist_grep "${search}" "$@"
}
function hist_grep_unique() {
  hist_grep "$@" | cut -f3 | awk '!x[$0]++'
}
