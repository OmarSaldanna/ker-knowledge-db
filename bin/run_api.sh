#!/bin/bash

# NOTE: THIS FILE IS EXECUTED BY KER FILE

# a message
echo \nRunning sdb_$1\n

# open a tmux session: activate the venv and run the api
# also name it as the sdb instance name
tmux new-session -d -s "sdb_$1" "source $PROJECT_PATH/venv/bin/activate python3 $PROJECT_PATH/api.py $1"