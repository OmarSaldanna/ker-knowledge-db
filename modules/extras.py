import os
import random
import hashlib

# used to read the flag file that indicates the curren sdb
def which_sdb ():
    try:
        with open(os.environ["FLAG_SDB_NAME"], 'r') as f:
            content = f.read()
        return content.strip()
    except:
        return ""

# used to change the flag file that indicates the curren sdb
def move_to_sdb (name):
    with open(os.environ["FLAG_SDB_NAME"], 'w') as f:
        f.write(name)

# function to generate hashes of a dicts
def hashx (string):
    hash_obj = hashlib.sha256()
    # convert the string to bytes and hash
    hash_obj.update(string.encode('utf-8'))
    # get the hex
    return str(hash_obj.hexdigest())[:random.randint(32, 128)]
    # return str(hash_obj.hexdigest())[:128]

# function to generate the ids based on content
def generate_id_and_source (documents, source):
    # in every document
    for doc in documents:
        # set also the source
        doc['source'] = source
        # generate an id based on the content
        doc['id'] = hashx(doc["content"] + doc["title"] + doc["source"])
    # and return documents
    return documents