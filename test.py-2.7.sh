#!/bin/bash

set -e
set -u

PYTHON="python2.7"
# shellcheck disable=SC2034
VENV="venv-2.7"

cd "$( dirname "$0" )"

if [[ -z $(type -p "${PYTHON}") ]] ; then
    echo "Could not found executable '${PYTHON}'." >&2
    exit 5
fi

RC_FILE="test.rc"

if [[ ! -f "${RC_FILE}" ]] ; then
    echo "Could not found resource file '${RC_FILE}'." >&2
    exit 5
fi

# shellcheck source=/dev/null
. "${RC_FILE}"
exec_tests

# vim: ts=4
