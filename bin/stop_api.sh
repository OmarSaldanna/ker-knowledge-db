#!/bin/bash

# NOTE: THIS FILE IS EXECUTED BY KER FILE

# kill the tmux session
tmux kill-session -t "sdb_$1"

# a message
echo \nStoppig sdb_$1\n

# show the active sessions
tmux ls

exit 0