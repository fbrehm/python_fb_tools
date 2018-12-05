#!/bin/bash

set -e
set -u

PYTHON="python3.5"
VENV="venv-3.5"

cd $( dirname $0 )

if [[ -z $(type -p "${PYTHON}") ]] ; then
    echo "Could not found executable '${PYTHON}'." >&2
    exit 5
fi

RC_FILE="test.rc"

if [[ ! -f "${RC_FILE}" ]] ; then
    echo "Could not found resource file '${RC_FILE}'." >&2
    exit 5
fi

. "${RC_FILE}"
exec_tests

# vim: ts=4
