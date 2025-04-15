#!/bin/bash

# create the collections dir
mkdir collections

# install the requirements
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip3 install -r requirements.txt

# make ker file executable
chmod 700 bin/ker

# make a link of the ker file to be executed
echo "-> Make a link into an executable path"
echo "ln bin/ker <a folder located in \$PATH>"
echo

# make the .keys file
echo "export OPENAI_API_KEY=" > .keys
echo "-> paste your OpenAI API KEY in .keys file"