#!/usr/bin/env bash

host=localhost
port=5000
device=uart0
direction=both
disconnectOnHalt=true
sendRequest=true

while [[ "$1" =~ ^- && ! "$1" == "--" ]]; do case $1 in
    -h | --host )
        shift; host=$1
        ;;
    -p | --port )
        shift; port=$1
        ;;
    -d | --device )
        shift; device=$1
        ;;
    --no-disconnect )
        disconnectOnHalt=false
        ;;
    --no-request )
        sendRequest=false
        ;;
    *)
        echo "Unknown option: $1"
        exit 1
esac; shift; done
if [[ "$1" == '--' ]]; then shift; fi

state=$(stty -g)
if [[ "$direction" == "tx" ]]; then
    stty raw opost
else
    stty raw opost -echo
fi

if [[ "$sendRequest" == "true" ]]; then
    {
        echo "{\"type\": \"serial\", \"device\": \"$device\", \"overrun\": false, \"direction\": \"$direction\", \"disconnectOnHalt\": $disconnectOnHalt}"
        cat
    } | netcat -v "$host" "$port"
else
    netcat -v "$host" "$port"
fi

stty "$state"

echo
