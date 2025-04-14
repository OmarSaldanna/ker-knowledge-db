#!/bin/bash

# create the collections dir
mkdir collections

# install the requirements
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip3 install -r requirements.txt

# make ker file executable
echo Make the file executable with
echo "chmod 700 bin/ker"

# make a link of the ker file to be executed
echo and make a link into an executable path
echo "ln bin/ker ~/bin/ker"