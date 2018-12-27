#!/bin/bash

MY_SLEEP="${1:-3}"
NORMAL_EXIT="n"

abort() {
    if [[ "${NORMAL_EXIT}" == "n" ]] ; then
        echo "Aborting by signal." >&2
        exit 5
    fi
}

echo "Starting $0 ..."
echo

trap abort INT TERM EXIT ABRT

echo "Sleeping ${MY_SLEEP} seconds."

i="${MY_SLEEP}"
while [[ "$i" -gt "0" ]] ; do
    printf "$i "
    i=$(( $i - 1 ))
    sleep 1
done

NORMAL_EXIT="y"
echo
echo "Wakeup"
echo "Finished."

# vim: ts=4 et
