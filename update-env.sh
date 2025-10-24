#!/bin/bash
# shellcheck disable=SC2317  # Don't warn about unreachable commands in this file

set -e
set -u

VERBOSE="n"
DEBUG="n"
QUIET='n'

VERSION="3.0"

# console colors:
RED=""
GREEN=""
YELLOW=""
# shellcheck disable=SC2034
BLUE=""
# shellcheck disable=SC2034
MAGENTA=""
CYAN=""
NORMAL=""

BASENAME=$( basename "${0}" )
BASE_DIR=$( dirname "$0" )
cd "${BASE_DIR}"
BASE_DIR=$( readlink -f . )
MAN_PARENT_DIR="data/share/man"

declare -a VALID_PY_VERSIONS=("3.13" "3.12" "3.11" "3.10" "3.9")
VENV='.venv'

PIP_OPTIONS=
export VIRTUAL_ENV_DISABLE_PROMPT=y

TMPFILE_GETVALUE=
TMPFILE_GETKEYS=
ENTRYPOINTS=''
DATA_DIR=

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
        RED=$( tput setaf 9 )
        GREEN=$( tput setaf 10 )
        YELLOW=$( tput setaf 11 )
        # shellcheck disable=SC2034
        BLUE=$( tput setaf 12 )
        # shellcheck disable=SC2034
        MAGENTA=$( tput setaf 13 )
        CYAN=$( tput setaf 14 )
        NORMAL=$( tput op )
    else
        RED=""
        YELLOW=""
        GREEN=""
        # shellcheck disable=SC2034
        BLUE=""
        # shellcheck disable=SC2034
        MAGENTA=""
        CYAN=""
        NORMAL=""
    fi

    local my_tty
    my_tty=$( tty )
    if [[ "${my_tty}" =~ 'not a tty' ]] ; then
        my_tty='-'
    fi

}
detect_color

#------------------------------------------------------------------------------
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
                shift
                ;;
            --nocolor)
                RED=""
                YELLOW=""
                GREEN=""
                # BLUE=""
                CYAN=""
                NORMAL=""
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

    if type -t msgfmt >/dev/null ; then
        :
    else
        error "Command '${RED}msgfmt${NORMAL}' not found, please install package '${YELLOW}gettext${NORMAL}' or appropriate."
        exit 6
    fi

    if [[ "${VERBOSE}" == "y" ]] ; then
        PIP_OPTIONS="--verbose"
    elif [[ "${QUIET}" == "y" ]] ; then
        PIP_OPTIONS="--quiet --quiet"
    else
        PIP_OPTIONS="--quiet"
    fi

}

#------------------------------------------------------------------------------
init_venv() {

    local py_version=
    local python=
    local found="n"

    empty_line
    line
    info "Preparing and using virtual environment '${CYAN}${VENV}${NORMAL}' …"
    empty_line


    if [[ ! -f "${VENV}/bin/activate" ]] ; then
        found="n"
        for py_version in "${VALID_PY_VERSIONS[@]}" ; do
            python="python${py_version}"
            debug "Testing Python binary '${CYAN}${python}${NORMAL}' …"
            if type -t "${python}" >/dev/null ; then
                found="y"
                empty_line
                info "Found '${GREEN}${python}${NORMAL}'."
                empty_line
                "${python}" -m venv "${VENV}"
                break
            fi
        done
        if [[ "${found}" == "n" ]] ; then
            empty_line >&2
            error "Did not found a usable Python version." >&2
            error "Usable Python versions are: ${YELLOW}${VALID_PY_VERSIONS[*]}${NORMAL}." >&2
            empty_line >&2
            exit 5
        fi
    fi

    # shellcheck disable=SC1091
    . "${VENV}/bin/activate" || exit 5

}

#------------------------------------------------------------------------------
RM() {

    local cmd="rm"
    if [[ "${VERBOSE}" == "y" ]] ; then
        cmd+=" --verbose"
    fi
    debug "Executing: ${cmd} $*"
    # shellcheck disable=SC2086,SC2294
    eval ${cmd} "$@"

}

#------------------------------------------------------------------------------
cleanup_awk_scripts() {

    debug "Cleaning up AWK scripts ..."

    if [[ -n "${TMPFILE_GETVALUE}" && -f "${TMPFILE_GETVALUE}" ]] ; then
        debug "Removing '${CYAN}${TMPFILE_GETVALUE}${NORMAL}' ..."
        RM "${TMPFILE_GETVALUE}"
    fi

    if [[ -n "${TMPFILE_GETKEYS}" && -f "${TMPFILE_GETKEYS}" ]] ; then
        debug "Removing '${CYAN}${TMPFILE_GETKEYS}${NORMAL}' ..."
        RM "${TMPFILE_GETKEYS}"
    fi

}

#------------------------------------------------------------------------------
create_awk_scripts() {

    line
    info "Creating AWK scripts for evaluating pyproject.toml."

    TMPFILE_GETVALUE=$( mktemp 'get-inifile-value-XXXXXXXX.awk' )
    TMPFILE_GETKEYS=$( mktemp 'get-inifile-keys-XXXXXXXX.awk' )

    trap cleanup_awk_scripts INT TERM EXIT ABRT

    lines=$( cat <<-EOF
		# Script for extracting a value from an INI-file
		#
		# Example for calling:
		# awk -f get_ini_value.awk -v target_section="[build-system]" -v key="build-backend" pyproject.toml

		BEGIN {
		  # Defaults
		  found_section = 0
		}

		{
		  # Strip leading and trailing white spaces
		  line = \$0
		  gsub(/^[ \t]+|[ \t]+\$/, "", line)

		  # Step comments and empty rows
		  if (line ~ /^;/ || line ~ /^#/) {
		    next
		  }
		  if (length(line) == 0) {
		    next
		  }

		  # Check for the correct section
		  if (line ~ /^\[.*\]\$/) {
		    section = substr(line, 2, length(line) - 2)
		    if (section == target_section) {
		      found_section = 1
		    } else {
		      found_section = 0
		    }
		    next
		  }

		  # If we are in the correct section
		  if (found_section == 1) {
		    if (line ~ "^" key "[ \t]*=.*") {
		      split(line, arr, /[ \t]*=[ \t]*/)

		      value = arr[2]

		      gsub(/^"|"\$/, "", value)
		      gsub(/^'|'\$/, "", value)

		      print value

		      exit
		    }
		  }
		}
		EOF
    )

    echo "${lines}" > "${TMPFILE_GETVALUE}"
    debug "Created '${CYAN}${TMPFILE_GETVALUE}${NORMAL}'."

    lines=$( cat <<-EOF
		# Script for extracting all keys of a section of an INI-file
		#
		# Example for calling:
		# awk -f get_ini_keys.awk -v target_section="project.scripts" pyproject.toml

		BEGIN {
		    in_section = 0
		}

		{
		    # Cleaning row: removing leading and trailing whitespaces and cut before comment character
		    line = \$0
		    sub(/^[ \t]+/, "", line)
		    sub(/[ \t]+\$/, "", line)
		    sub(/[ \t]*[#;].*\$/, "", line)

		    # Skip on empty row
		    if (line == "") {
		        next
		    }

		    # Check for section header
		    if (line ~ /^\[.*\]\$/) {
		        section = substr(line, 2, length(line) - 2)
		        if (section == target_section) {
		            in_section = 1
		        } else {
		            in_section = 0
		        }
		        next
		    }

		    # Perform key-value-pair in target section
		    if (in_section == 1) {
		        if (line ~ /^[a-zA-Z0-9_-]+[ \t]*=[ \t]*.*\$/) {
		            # extract and print key
		            split(line, a, /[ \t]*=[ \t]*/)
		            print a[1]
		        }
		    }
		}
		EOF
    )

    echo "${lines}" > "${TMPFILE_GETKEYS}"
    debug "Created '${CYAN}${TMPFILE_GETKEYS}${NORMAL}'."

}

#------------------------------------------------------------------------------
upgrade_pip() {
    line
    info "Upgrading PIP …"
    empty_line
    # shellcheck disable=SC2086
    pip install ${PIP_OPTIONS} --upgrade --upgrade-strategy eager pip
    empty_line
}

#------------------------------------------------------------------------------
upgrade_flit() {
    line
    info "Upgrading flit + wheel + six …"
    empty_line
    # shellcheck disable=SC2086
    pip install ${PIP_OPTIONS} --upgrade --upgrade-strategy eager flit wheel six
    empty_line
}

#------------------------------------------------------------------------------
install_modules_by_flit() {
    line
    info "Installing all necessary packages with flit ..."
    empty_line
    flit install --only-deps --deps all --python "${VENV}/bin/python3"
}

#------------------------------------------------------------------------------
upgrade_modules() {
    local packages=''
    local package=''

    line
    info "Installing and/or upgrading necessary modules …"
    empty_line
    packages=$( pip3 list --outdated --exclude-editable --format json 2>/dev/null  | jq -r .[].name )
    if [[ -n "${packages}" ]] ; then
        msg="Packages to update:"
        for package in ${packages} ; do
            msg+="\n * ${CYAN}${package}${NORMAL}"
        done
        info "${msg}"
        empty_line
        # shellcheck disable=SC2086
        pip install ${PIP_OPTIONS} --upgrade --upgrade-strategy eager ${packages}
    else
        info "No packages to update found."
    fi
}

#------------------------------------------------------------------------------
install_local_package() {

    line
    info "Installing local package into '${CYAN}${VENV}${NORMAL}' …"
    empty_line
    info "Ensuring directory '${CYAN}${MAN_PARENT_DIR}${NORMAL}' …"
    mkdir -pv "${MAN_PARENT_DIR}"

    empty_line
    flit install --symlink --deps production --python "${VENV}/bin/python3"

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
eval_entrypoints() {

    line
    info "Get all entrypoints ..."
    ENTRYPOINTS=''
    local entrypoint
    local cmd
    local result

    cmd="awk -f '${TMPFILE_GETKEYS}' -v target_section=project.scripts pyproject.toml"
    debug "Calling ${cmd}"
    # shellcheck disable=SC2086,SC2294
    result=$( eval ${cmd} )
    debug "Got raw entrypoints from AWK script: '${result}'"

    if [[ -n "${result}" ]] ; then
        debug "Evaluate entrypoints ..."
        for entrypoint in ${result}; do
            if [[ -n "${ENTRYPOINTS}" ]] ; then
                ENTRYPOINTS+=" "
            fi
            ENTRYPOINTS+="${entrypoint}"
        done
    fi

    if [[ -n "${ENTRYPOINTS}" ]] ; then
        info "Found entrypoints: ${CYAN}${ENTRYPOINTS}${NORMAL}"
    else
        info "Did not found any entrypoints."
    fi

}

#------------------------------------------------------------------------------
eval_datadir() {

    line
    info "Get directory for external data."

    DATA_DIR=''

    cmd="awk -f '${TMPFILE_GETVALUE}' -v target_section=tool.flit.external-data -v key=directory pyproject.toml"
    debug "Calling ${cmd}"
    # shellcheck disable=SC2086,SC2294
    DATA_DIR=$( eval ${cmd} )

    if [[ -n "${DATA_DIR}" ]] ; then
        info "Found data directory: '${CYAN}${DATA_DIR}${NORMAL}'"
    else
        info "Did not found data directory."
    fi

}

#------------------------------------------------------------------------------
ensure_datadir() {

    if [[ -z "${DATA_DIR}" ]] ; then
        return 0
    fi

    line
    info "Ensuring directory for external data '${CYAN}${DATA_DIR}${NORMAL}' ..."

    if [[ -e "${DATA_DIR}" ]] ; then
        if [[ -d "${DATA_DIR}" ]] ; then
            return 0
        fi
        error "Path exists, but is not a directory."
        exit 7
    fi

    info "Creating directory '${CYAN}${DATA_DIR}${NORMAL}' ..."
    mkdir --parent --verbose "${DATA_DIR}"

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
    create_awk_scripts
    eval_entrypoints
    eval_datadir
    ensure_datadir
    init_venv
    upgrade_pip
    upgrade_flit
    install_modules_by_flit
    upgrade_modules
    install_local_package
    list_modules
    compile_i18n

    line
    info "Finished."
    empty_line

}

main "$@"

exit 0

# vim: ts=4 list
