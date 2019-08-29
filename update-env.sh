#!/bin/bash

base_dir=$( dirname "$0" )
cd "${base_dir}" || exit 99
base_dir=$( readlink -f . )

declare -a VALID_PY_VERSIONS=("3.8" "3.7" "3.6" "3.5")

echo "Preparing virtual environment ..."
echo
if [[ ! -f venv/bin/activate ]] ; then
    found="n"
    for py_version in "${VALID_PY_VERSIONS[@]}" ; do
        PYTHON="python${py_version}"
        if type -t "${PYTHON}" >/dev/null ; then
            found="y"
            echo
            echo "Found ${PYTHON}."
            echo
            virtualenv --python="${PYTHON}" venv
            break
        fi
    done
    if [[ "${found}" == "n" ]] ; then
        echo >&2
        echo "Did not found a usable Python version." >&2
        echo "Usable Python versions are: ${VALID_PY_VERSIONS[*]}" >&2
        echo >&2
        exit 5
    fi
fi

# shellcheck source=/dev/null
. venv/bin/activate || exit 5

echo "---------------------------------------------------"
echo "Installing and/or upgrading necessary modules ..."
echo
pip install --upgrade --upgrade-strategy eager --requirement requirements.txt
echo
echo "---------------------------------------------------"
echo "Installed modules:"
echo
pip list --format columns

if [[ -x compile-xlate-msgs.sh ]]; then
    echo
    echo "--------------"
    echo "Updating i18n files in ${base_dir} ..."
    echo
    ./compile-xlate-msgs.sh 
fi

echo
echo "-------"
echo "Fertig."
echo

# vim: ts=4
