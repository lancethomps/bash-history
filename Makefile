PY_PACKAGE := bashhistory
PY_PATHS := $(PY_PACKAGE) $(PY_PACKAGE)tests

include Makefile.common-bash
include Makefile.common-python

debug::
	shellcheck --version

ci: lint test-parallel

