import os
import sys
import json
import shutil
import pyperclip
from typing import List, Dict

# import modules
from modules.llm import chat
from modules.db import new_sdb, SDB
from modules.scrapper import get_content
from modules.extras import move_to_sdb, which_sdb

# the main path of the project
main_path = os.environ["COLLECTIONS_PATH"]
# current dir, from where ker where executed
current_dir = os.environ["CURRENT_PATH"] + "/"
# get the current database
# current_sdb = which_sdb()

# main command handler
class Brain:

    def __init__(self):
        # map commands to their handling methods
        self.commands = {
            'mv': self.handle_mv,
            'move': self.handle_mv,
            'ls': self.handle_ls,
            'create': self.handle_create,
            'rm': self.handle_rm,
            'remove': self.handle_rm,
            'add': self.handle_add,
            'set': self.handle_set,
            'chat': self.handle_use,
            'chate': self.handle_usem,
            'start': self.handle_start,
            'stop': self.handle_stop
            # help command is considered on bin/ker
        }

    def __call__ (self, args: List[str]):
        # if the command was found
        if args[0] in self.commands.keys():
            # do it
            self.commands[args[0]](args[1:])
        else:
            print('\033[91m' + "Unknown comand, type: " + '\033[0m' + "ker help" + '\033[91m' + " for more" + '\033[0m')
            return

    def _load_config (self, name: str):
        self.config = {}
        # open the file
        with open(main_path + name + "/config.json", "r") as f:
            # and save the content
            self.config = json.load(f)

################################################################################

    # create an sdb
    def handle_create(self, args: List[str]) -> str:
        # if there's no name
        if len(args) != 1:
            if len(args) < 1:
                print('\033[91m' + "SDB name not provided" + '\033[0m')
                return
            # or more than one
            else:
                print('\033[91m' + "Can create only one SDB at time" + '\033[0m')
                return
        # get the name of the db
        name = args[0]
        # create the db
        new_sdb(name)
        # and move to it
        print("Moving to " + '\033[94m' + name + '\033[0m')
        move_to_sdb(name)
    
    # move to another sdb
    def handle_mv (self, args: List[str]) -> str:
        # if there's no name
        if len(args) != 1:
            if len(args < 1):
                print('\033[91m' + "SDB name not provided" + '\033[0m')
                return
            # or more than one
            else:
                print('\033[91m' + "Can only move to one SDB at time" + '\033[91m')
                return
        # get the name of the db
        name = args[0]
        # check if it exists
        if name not in os.listdir(main_path):
            print('\033[91m' + "SDB " + '\033[0m' + name + '\033[91m' +" not found" + '\033[0m')
            return
        # and save it
        print("Moving to " + '\033[94m' + name + '\033[0m')
        move_to_sdb(name)

    # remove sdb
    def handle_rm (self, args: List[str]) -> str:
        # if there's no name
        if len(args) != 1:
            if len(args < 1):
                print('\033[91m' + "SDB name not provided" + '\033[0m')
                return
            # or more than one
            else:
                print('\033[91m' + "Can only remove to one SDB at time" + '\033[91m')
                return
        # get the name of the db
        name = args[0]
        # check if it exists
        if name not in os.listdir(main_path):
            print('\033[91m' + "SDB " + '\033[0m' + name + '\033[91m' + " not found" + '\033[0m')
            return
        # then try to remove it
        try:
            # remove
            shutil.rmtree(main_path + name)
            print('\033[92m' + "Removed " + name + '\033[0m')
            # and remove the current
            move_to_sdb("")
        # in case of error
        except OSError as e:
            print('\033[91m' + "Error removing" + '\033[0m' + name + f":\n{e}")

    # list sdbs
    def handle_ls (self, args: List[str]) -> str:
        # if name was passed
        if len(args) > 0:
            name = args[0]
            # check if the name is in collections
            if name in os.listdir(main_path):
                print('\033[92m' + "Files included in \033[0m" + name + ":")
                # then check the included file
                with open(main_path + name + "/included.txt", 'r') as f:
                    for line in f:
                        print('\t'+line, end='')
            # if collection not found
            else:
                print('\033[91m' + "Not found collection: "+ '\033[0m' + name)
        # else: list available dbs
        else:
            print('\033[92m' + "Available SDBs:" + '\033[0m')
            for db in os.listdir(main_path):
                if not db.startswith("."):
                    print(f"\t- {db}")

################################################################################
    
    # add content to database
    def handle_add (self, args: List[str]) -> str:
        # locate the db
        name = which_sdb()
        if name == "":
            print('\033[91m' + "SDB not selected, use: " + f'\033[0mker mv [SDB name]')
            return
        # then there are content to add
        print('\033[92m' + "Adding memories to " + '\033[0m' + name + '\033[92m' + "..." + '\033[0m\n')
        # instance the db
        sdb = SDB(name)
        # counter of items
        added_count = 0
        # for each file get the content
        for file in args:
            # try:
            # get the file content
            content, new_path = get_content(file, current_dir, name)
            # and let the db add the content
            added = sdb.add_documents(content)
            # if it's correct, then save the file in assets
            if added > 0:
                # copy the file to assets
                shutil.copyfile(current_dir + file, new_path)
                # count items
                added_count += added
                # and add the file name to a collection log
            # except Exception as e:
                # print('\033[91m' + "Error processing file " + f'\033[0m {file}:', e)
        # finally
        print('\n\033[92m' + f"Added {added_count} items to \033[0m{name}")

    # copy the path to settings file
    def handle_set (self, args: List[str]) -> str:
        # check if a name was given
        if len(args) > 0:
            name = args[0]
            # check if name is in sdb
            if name in os.listdir(main_path):
                # then copy the path to settings file
                settings_file = main_path + name + "/config.json"
                pyperclip.copy(settings_file)
                # and a message
                print('\033[92m' + "Path to config file copied to clipboard: " + '\033[0m' + settings_file)
            # if collection not found
            else:
                print('\033[91m' + "Not found collection: "+ '\033[0m' + name)
        # if no command given
        else:
            print('\033[91m' + "Missing SDB name"+ '\033[0m')

################################################################################

    # start a chat with llm and embedding
    def handle_use (self, args: List[str]) -> str:
        # use the embeddings chat but with llm
        self.handle_usem(args, llm=True)

    # start a chat with only embedding
    def handle_usem (self, args: List[str], llm=False) -> str:
        # locate the db
        name = which_sdb()
        if name == "":
            print('\033[91m' + "SDB not selected, use: " + f'\033[0mker mv [SDB name]')
            return
        # then get the number of coincidences
        coincidences = int(os.environ["DEFAULT_COINCIDENCES"])
        # check if it was given
        try:
            # get it from the args
            coincidences = int(args[0])
        except:
            pass
        os.system("clear")
        # if it's llm, then load the config
        self._load_config(name)
        # then start the db
        print('\033[92m' + "Embedding Chat on: \033[0m" + name + '\n')
        sdb = SDB(name)
        # start the chat
        while True:
            # get the prompt
            question = input("\n\033[95m>>> Prompt~$ \033[0m")
            # an empty message
            if not question:
                continue
            # to end the chat
            if question in ["q", ";", "bye"]:
                print("\n\033[92m >>> Ker~$ Byee! \033[0m", end='')
                break
            # this to clear the chat
            if question == "clear":
                os.system("clear")
                continue
            # then make the query
            res = sdb.query(question, coincidences)
            # only get the content
            context = [json.loads(r.replace("'", "\""))["content"] for r in res]

            # to answer without llm
            if not llm:
                # print results
                print("\n")
                for c in context:
                    print(c)
                    print("\n","*****"*10, "\n")

            # or answer with llm
            else:
                # create a system message
                prompt = "\n".join(self.config["system"])
                # and insert question and context
                prompt = prompt.replace("{*question}", question)
                # for content we need to use only the text
                prompt = prompt.replace("{*context}", "\n\n".join(context))
                # then chat
                print("\n\033[92m>>> Ker~$ \033[0m", end='')
                print(chat(self.config["llm"], prompt))
                print("\n")

################################################################################

    # start the api
    def handle_start (self, args: List[str]) -> str:
        return "on"

    # stop an api
    def handle_stop (self, args: List[str]) -> str:
        return "on"


if __name__ == "__main__":
    print()
    # validate the first argument
    if len(sys.argv) < 1:
        print('\033[91m' + "Unknown comand, type: " + '\033[0m' + "ker help" + '\033[91m' + " for more" + '\033[0m')
    else:
        # instance the Ker brain
        ker = Brain()
        # Extract command and arguments from command line
        args = sys.argv[1:]
        # Process the command
        ker(args)
    print()