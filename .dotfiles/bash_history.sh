#!/usr/bin/env bash
################################################################### SETUP ########################################################################
S="${BASH_SOURCE[0]}" && while [ -h "$S" ]; do D="$(cd -P "$(dirname "$S")" && pwd)" && S="$(readlink "$S")" && [[ $S != /* ]] && S="$D/$S"; done; _SCRIPT_DIR="$(cd -P "$(dirname "$S")" && pwd)" && unset S D
##################################################################################################################################################

##################################################################################################################################################
#################################################################### CONFIG ######################################################################
##################################################################################################################################################

BASH_HIST_LOGS="${BASH_HIST_LOGS:-$HOME/.logs/bash_history}"
BASH_HIST_ADD_ALIASES="${BASH_HIST_ADD_ALIASES:-false}"
BASH_HIST_MAX_WIDTH="${BASH_HIST_MAX_WIDTH:-225}"
BASH_HIST_NO_SQLITE="${BASH_HIST_NO_SQLITE:-false}"
BASH_HIST_ADD_TO_DB="${BASH_HIST_ADD_TO_DB:-false}"
BASH_HIST_IGNORE_MISSING_DB="${BASH_HIST_IGNORE_MISSING_DB:-false}"
BASH_HIST_SELECT_LIMIT="${BASH_HIST_SELECT_LIMIT:-50}"

unalias hg hgc hge hgp hgu > /dev/null 2>&1 || true

##################################################################################################################################################
################################################################# VANILLA BASH ###################################################################
##################################################################################################################################################

_BH_FUNCS=(
  hist
  hist_grep
  hist_grep_copy
  hist_grep_exec
  hist_grep_pwd
  hist_grep_unique
)
unset -f "${_BH_FUNCS[@]}" > /dev/null 2>&1 || true
source "${_SCRIPT_DIR}/.bash_history_vanilla_bash.sh"

##################################################################################################################################################
############################################################### CHECK FOR SQLITE #################################################################
##################################################################################################################################################
function _bh_has_python() {
  if command -v python3 > /dev/null 2>&1 && [[ "$(python3 -V)" == 'Python 3'* ]]; then
    return 0
  fi
  if command -v python > /dev/null 2>&1 && [[ "$(python -V)" == 'Python 3'* ]]; then
    return 0
  fi
  return 1
}

function _bh_using_sqlite() {
  test "${_BASH_HIST_USING_SQLITE}" = "true"
}

_BASH_HIST_USING_SQLITE=true
if test "${BASH_HIST_NO_SQLITE}" = "true" || ! command -v hist_db_insert > /dev/null 2>&1 || ! command -v hist_grep > /dev/null 2>&1 || ! _bh_has_python; then
  _BASH_HIST_USING_SQLITE=false
fi

##################################################################################################################################################
################################################################# PROMPT SETUP ###################################################################
##################################################################################################################################################

if test "${BASH_HIST_NO_WRITE:-}" = 'true'; then
  true
elif test -w "$HOME"; then
  if test -z "${ORIG_PROMPT_COMMAND:-}"; then
    export ORIG_PROMPT_COMMAND="${PROMPT_COMMAND:- }"
  else
    export PROMPT_COMMAND="$ORIG_PROMPT_COMMAND"
  fi

  if _bh_using_sqlite && test "${BASH_HIST_ADD_TO_DB}" != "true"; then
    # shellcheck disable=SC2016
    log_cmd='hist_db_insert --exit-code "$?" --pid "$$" --command "$(HISTTIMEFORMAT= history 1 2>/dev/null)"'
  else
    # shellcheck disable=SC2016
    log_cmd='bash_history_log_to_file --exit-code $? --pid $$ --command "$(HISTTIMEFORMAT= history 1 2>/dev/null)"'
    if test "${BASH_HIST_ADD_TO_DB}" = "true"; then
      log_cmd="${log_cmd} --add-to-db"
    fi
    if test "${BASH_HIST_IGNORE_MISSING_DB}" = "true"; then
      log_cmd="${log_cmd} --ignore-missing-db"
    fi
  fi
  if test "$(id -u)" -ne 0; then
    ! test -d "$BASH_HIST_LOGS" && mkdir -p "$BASH_HIST_LOGS"
    export PROMPT_COMMAND="${log_cmd}; ${PROMPT_COMMAND}"
  elif current_user=$(/bin/ls -l /dev/console | /usr/bin/awk '{ print $3 }'); then
    ! test -d "$BASH_HIST_LOGS" && sudo -u "$current_user" mkdir -p "$BASH_HIST_LOGS"
    export PROMPT_COMMAND="${log_cmd}; ${PROMPT_COMMAND}"
  else
    echo "Running as root and current logged in user could not be determined, not writing history logs..."
  fi
else
  echo "It appears your home directory is read only, not writing history logs there..."
fi

##################################################################################################################################################
########################################################## USE VANILLA BASH IF NEEDED ############################################################
##################################################################################################################################################

if ! _bh_using_sqlite; then
  for _bh_func in "${_BH_FUNCS[@]}"; do
    eval "function ${_bh_func}() { _bh_vanilla_${_bh_func} \"\$@\"; }"
  done
fi

##################################################################################################################################################
################################################################## ADD ALIASES ###################################################################
##################################################################################################################################################

if test "${BASH_HIST_ADD_ALIASES-}" = "true"; then
  alias hg='hist_grep'
  alias hgc='hist_grep_copy'
  alias hge='hist_grep_exec'
  if _bh_using_sqlite; then
    alias hgp='hist_grep --pwd'
    alias hgu='hist_grep --unique'
  else
    alias hgp='hist_grep_pwd'
    alias hgu='hist_grep_unique'
  fi
fi

##################################################################################################################################################
#################################################################### CLEANUP #####################################################################
##################################################################################################################################################

unset -v \
  current_user \
  log_cmd \
  _bh_func \
  _BH_FUNCS \
  _BASH_HIST_USING_SQLITE

unset -f \
  _bh_has_python \
  _bh_using_sqlite
