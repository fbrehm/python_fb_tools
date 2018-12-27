#!/bin/bash

MY_SLEEP="${1:-3}"

echo "Starting $0 ..."
echo
echo "Sleeping ${MY_SLEEP} seconds."
sleep ${MY_SLEEP}
echo "Wakeup"
echo "Finished."

# vim: ts=4 et
