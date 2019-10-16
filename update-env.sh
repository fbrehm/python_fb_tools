#!/bin/bash

set -e
set -u

VERBOSE="n"
DEBUG="n"
QUIET='n'

VERSION="2.3"

# console colors:
RED=""
YELLOW=""
GREEN=""
# BLUE=""
CYAN=""
NORMAL=""

BASENAME=$(basename "${0}")
BASE_DIR=$( dirname "$0" )
cd "${BASE_DIR}" || exit 99
BASE_DIR=$( readlink -f . )

PIP_OPTIONS=
export VIRTUAL_ENV_DISABLE_PROMPT=y

declare -a VALID_PY_VERSIONS=("3.8" "3.7" "3.6" "3.5")
PY_VERSION_FINAL=
PYTHON=
VENV_BIN='virtualenv'

#-------------------------------------------------------------------
detect_color() {

    local safe_term="${TERM//[^[:alnum:]]/?}"
    local match_lhs=""
    local use_color="false"
    local term=

    if [[ -f ~/.dir_colors   ]] ; then
        match_lhs="${match_lhs}$( grep '^TERM ' ~/.dir_colors | sed -e 's/^TERM  *//' -e 's/ .*//')"
    fi
    if [[ -f /etc/DIR_COLORS   ]] ; then
        match_lhs="${match_lhs}$( grep '^TERM ' /etc/DIR_COLORS | sed -e 's/^TERM  *//' -e 's/ .*//')"
    fi
    if [[ -z ${match_lhs} ]] ; then
        type -P dircolors >/dev/null && \
        match_lhs=$(dircolors --print-database | grep '^TERM ' | sed -e 's/^TERM  *//' -e 's/ .*//')
    fi
    for term in ${match_lhs} ; do
        # shellcheck disable=SC2053
        if [[ "${safe_term}" == ${term} || "${TERM}" == ${term} ]] ; then
            use_color="true"
            break
        fi
    done

    # console colors:
    if [ "${use_color}" = "true" ] ; then
        RED="\033[38;5;196m"
        YELLOW="\033[38;5;226m"
        GREEN="\033[38;5;46m"
        # BLUE="\033[38;5;27m"
        CYAN="\033[38;5;36m"
        NORMAL="\033[39m"
        # HAS_COLORS="y"
    else
        RED=""
        YELLOW=""
        GREEN=""
        # BLUE=""
        CYAN=""
        NORMAL=""
    fi

    local my_tty

    my_tty=$(tty)
    if [[ "${my_tty}" =~ 'not a tty' ]] ; then
        my_tty='-'
    fi

}
detect_color

my_date() {
    date +'%F %T.%N %:::z'
}

#------------------------------------------------------------------------------
debug() {
    if [[ "${VERBOSE}" != "y" ]] ; then
        return 0
    fi
    echo -e " * [$(my_date)] [${BASENAME}:${CYAN}DEBUG${NORMAL}]: $*" >&2
}

#------------------------------------------------------------------------------
info() {
    if [[ "${QUIET}" == "y" ]] ; then
        return 0
    fi
    if [[ "${VERBOSE}" == "y" ]] ; then
        echo -e " ${GREEN}*${NORMAL} [$(my_date)] [${BASENAME}:${GREEN}INFO${NORMAL}] : $*"
    else
        echo -e " ${GREEN}*${NORMAL} $*"
    fi
}

#------------------------------------------------------------------------------
warn() {
    if [[ "${VERBOSE}" == "y" ]] ; then
        echo -e " ${YELLOW}*${NORMAL} [$(my_date)] [${BASENAME}:${YELLOW}WARN${NORMAL}] : $*" >&2
    else
        echo -e " ${YELLOW}*${NORMAL} [${BASENAME}:${YELLOW}WARN${NORMAL}] : $*" >&2
    fi
}

#------------------------------------------------------------------------------
error() {
    if [[ "${VERBOSE}" == "y" ]] ; then
        echo -e " ${RED}*${NORMAL} [$(my_date)] [${BASENAME}:${RED}ERROR${NORMAL}]: $*" >&2
    else
        echo -e " ${RED}*${NORMAL} [${BASENAME}:${RED}ERROR${NORMAL}]: $*" >&2
    fi
}

#------------------------------------------------------------------------------
description() {
    cat <<-EOF
	Updates the Python virtual environment.

	EOF

}

#------------------------------------------------------------------------------
line() {
    if [[ "${QUIET}" == "y" ]] ; then
        return 0
    fi
    echo "---------------------------------------------------"
}

#------------------------------------------------------------------------------
empty_line() {
    if [[ "${QUIET}" == "y" ]] ; then
        return 0
    fi
    echo
}

#------------------------------------------------------------------------------
usage() {

    cat <<-EOF
	Usage: ${BASENAME} [-d|--debug] [[-v|--verbose] | [-q|--quiet]] [--nocolor]
	       ${BASENAME} [-h|--help]
	       ${BASENAME} [-V|--version]

	    Options:
	        -d|--debug      Debug output (bash -x).
	        -v|--verbose    Set verbosity on.
	        -q|--quiet      Quiet execution. Mutually exclusive to --verbose.
	        --nocolor       Don't use colors on display.
	        -h|--help       Show this output and exit.
	        -V|--version    Prints out version number of the script and exit.

	EOF

}

#------------------------------------------------------------------------------
get_options() {

    local tmp=
    local short_options="dvqhV"
    local long_options="debug,verbose,quiet,help,version"
    local py_version=
    local py_found="n"
    local ret=

    set +e
    tmp=$( getopt -o "${short_options}" --long "${long_options}" -n "${BASENAME}" -- "$@" )
    ret="$?"
    if [[ "${ret}" != 0 ]] ; then
        echo "" >&2
        usage >&2
        exit 1
    fi
    set -e

    # Note the quotes around `$TEMP': they are essential!
    eval set -- "${tmp}"

    while true ; do
        case "$1" in
            -d|--debug)
                DEBUG="y"
                shift
                ;;
            -v|--verbose)
                VERBOSE="y"
                shift
                ;;
            -q|--quiet)
                QUIET="y"
                RED=""
                YELLOW=""
                GREEN=""
                # BLUE=""
                CYAN=""
                NORMAL=""
                # HAS_COLORS="n"
                shift
                ;;
            --nocolor)
                RED=""
                YELLOW=""
                GREEN=""
                # BLUE=""
                CYAN=""
                NORMAL=""
                # HAS_COLORS="n"
                shift
                ;;
            -h|--help)
                description
                echo
                usage
                exit 0
                ;;
            -V|--version)
                echo "${BASENAME} version: ${VERSION}"
                exit 0
                ;;
            --) shift
                break
                ;;
            *)  echo "Internal error!"
                exit 1
                ;;
        esac
    done

    if [[ "${DEBUG}" = "y" ]] ; then
        set -x
    fi

    if [[ "${VERBOSE}" == "y" && "${QUIET}" == "y" ]] ; then
        error "Options '${RED}--verbose${NORMAL}' and '${RED}--quiet${NORMAL}' are mutually exclusive."
        echo >&2
        usage >&2
        exit 1
    fi

    py_found="n"
    info "Searching for valid Python …"
    for py_version in "${VALID_PY_VERSIONS[@]}" ; do
        PYTHON="python${py_version}"
        debug "Testing Python binary '${CYAN}${PYTHON}${NORMAL}' …"
        if type -t "${PYTHON}" >/dev/null ; then
            py_found="y"
            PY_VERSION_FINAL="${py_version}"
            empty_line
            info "Found '${GREEN}${PYTHON}${NORMAL}'."
            break
        fi
    done

    if [[ "${py_found}" == "n" ]] ; then
        empty_line >&2
        error "Did not found a usable Python version." >&2
        error "Usable Python versions are: ${YELLOW}${VALID_PY_VERSIONS[*]}${NORMAL}." >&2
        empty_line >&2
        exit 5
    fi

    info "Searching for valid virtualenv …"
    VENV_BIN="virtualenv-${PY_VERSION_FINAL}"
    debug "Testing '${VENV_BIN}' …"
    if type -t "${VENV_BIN}" >/dev/null ; then
        :
    else
        VENV_BIN="virtualenv"
        debug "Testing '${VENV_BIN}' …"
        if type -t "${VENV_BIN}" >/dev/null ; then
            :
        else
            empty_line >&2
            error "Did not found a usable virtualenv." >&2
            error "Command '${RED}virtualenv${NORMAL}' not found, please install package '${YELLOW}python-virtualenv${NORMAL}' or appropriate."
            empty_line >&2
            exit 6
        fi
    fi
    info "Found '${GREEN}${VENV_BIN}${NORMAL}'."

    if type -t msgfmt >/dev/null ; then
        :
    else
        echo "Command '${RED}msgfmt${NORMAL}' not found, please install package '${YELLOW}gettext${NORMAL}' or appropriate." >&2                                                                                             
        exit 6
    fi

    if [[ "${VERBOSE}" == "y" ]] ; then
        PIP_OPTIONS="--verbose"
    elif [[ "${QUIET}" == "y" ]] ; then
        PIP_OPTIONS="--quiet"
    fi

}

#------------------------------------------------------------------------------
init_venv() {

    empty_line
    line
    info "Preparing virtual environment …"
    empty_line


    if [[ ! -f venv/bin/activate ]] ; then

        empty_line
        if [[ "${VENV_BIN}" == 'virtualenv' ]] ; then
            virtualenv --python="${PYTHON}" venv
        else
            ${VENV_BIN} venv
        fi

    fi

    . venv/bin/activate || exit 5
    debug "Which pip:    $(which pip)"
    debug "Which python: $(which python)"

}

#------------------------------------------------------------------------------
upgrade_pip() {
    line
    info "Upgrading PIP …"
    empty_line
    pip install ${PIP_OPTIONS} --upgrade --upgrade-strategy eager pip
    empty_line
}

#------------------------------------------------------------------------------
upgrade_setuptools() {
    line
    info "Upgrading setuptools + wheel + six …"
    empty_line
    pip install ${PIP_OPTIONS} --upgrade --upgrade-strategy eager setuptools wheel six
    empty_line
}

#------------------------------------------------------------------------------
upgrade_modules() {
    line
    info "Installing and/or upgrading necessary modules …"
    empty_line
    pip install ${PIP_OPTIONS} --upgrade --upgrade-strategy eager --requirement requirements.txt
    empty_line
}

#------------------------------------------------------------------------------
list_modules() {
    if [[ "${QUIET}" == "y" ]] ; then
        return 0
    fi
    line
    info "Installed modules:"
    empty_line
    pip list --format columns
    empty_line
}

#------------------------------------------------------------------------------
compile_i18n() {

    if [[ -x compile-xlate-msgs.sh ]]; then
        line
        info "Updating i18n files in ${BASE_DIR} …"
        empty_line
        ./compile-xlate-msgs.sh
        empty_line
    fi
}

#------------------------------------------------------------------------------
compile_i18n() {

    if [[ -x compile-xlate-msgs.sh ]]; then
        line
        info "Updating i18n files in ${BASE_DIR} …"
        empty_line
        ./compile-xlate-msgs.sh
        empty_line
    fi
}

################################################################################
##
## Main
##
################################################################################

#------------------------------------------------------------------------------
main() {

    get_options "$@"
    init_venv
    upgrade_pip
    upgrade_setuptools
    upgrade_modules
    list_modules
    compile_i18n

    line
    info "Fertig."
    empty_line

}

main "$@"

exit 0

# vim: ts=4
