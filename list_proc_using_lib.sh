#!/bin/bash

if [ "$1" == "" ]; then
    echo "usage: $0 <lib absolute path>"
    exit 1
fi

./libs.py find_open $1 |xargs -I{} bash -c 'echo -ne "{}\t\t"; readlink -f /proc/{}/exe' # | sort
