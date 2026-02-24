#!/bin/bash

echo "Starting $0 ..."
echo
printf "Output without newline: "
sleep 2
echo
echo
echo "Output to STDOUT ..."
echo "Sleeping 3 seconds."
sleep 3
echo "Wakeup"
echo "Output to STDERR ..." >&2
echo "Sleeping 2 seconds."
sleep 2
echo "Finished."

# vim: ts=4 et
