#!/bin/bash

state=$(stty -g)
if [[ "${DIRECTION:=both}" == "tx" ]]; then
    stty raw opost
else
    stty raw opost -echo
fi

{
    echo "{\"type\": \"serial\", \"device\": \"uart0\", \"overrun\": false, \"direction\": \"${DIRECTION}\", \"disconnectOnHalt\": true}"
    cat
} | netcat -v "${HOST:=localhost}" "${PORT:=5000}"

stty "$state"

echo
