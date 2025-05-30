import os
import json
import ollama
import hashlib
import chromadb
from tqdm import tqdm

# function to add ids and source to the documents
from modules.extras import generate_id_and_source
from modules.embeddings import make_embeddings


# collection
#  |--- config.json
#  |--- assets/
#         |---- every file added ...

class SDB:
    def __init__ (self, name: str):
        # Base path where all collections are stored
        base_path = os.environ["COLLECTIONS_PATH"]
        # Full path to the specific database (collection)
        db_path = os.path.join(base_path, name, "db")
        # Create the directory if it doesn't exist (i.e., first time using this name)
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        # Initialize ChromaDB persistent client with this specific path
        self.client = chromadb.PersistentClient(path=db_path)
        # Get or create a collection with the given name
        self.collection = self.client.get_or_create_collection(name=name)
        # also load the config and the db dir
        self.dir = os.environ["COLLECTIONS_PATH"] + name + "/"
        with open(self.dir + "config.json", 'r') as f:
            self.config = json.load(f)

    def _generate_embeddings (self, text: str):
        # use the preset model to make the embeddings
        return make_embeddings(self.config["embedding"], text)

    def add_documents (self, content: list):
        # parameters for chromadb
        embeddings = []
        ids = []
        docs = []
        for doc in tqdm(content, desc="Embedding document"):
            # add the embedding based on the document content
            embeddings.append(self._generate_embeddings(doc["content"]))
            # the id
            ids.append(doc['id'])
            # and the content
            docs.append(json.dumps(doc, indent=4, ensure_ascii=False))
        # check if any of the documents already exist
        exist_first = self.collection.get(ids=ids[0])['documents']
        exist_last = self.collection.get(ids=ids[-1])['documents']
        # 
        if exist_first and exist_last:
            print('\033[93m' + ">>> coincidence on SDB, skipping..." + '\033[0m\n')
            return 0
        else:
            # and add to collection
            self.collection.add(ids=ids, documents=docs, embeddings=embeddings)
            return len(ids)

    def query (self, query_text: str, n_results: int):
        # make a query to the db
        query_embedding = self._generate_embeddings(query_text)
        # fetch results from the db
        results = self.collection.query(query_embeddings=[query_embedding], n_results=n_results)
        # if there were not results
        if 'documents' not in results:
            return []
        # else get the results
        results = results['documents'][0]
        # parse to json and return
        return [json.loads(r.replace("'", "\"")) for r in results]


# function to create db
def new_sdb (name: str):
    # try to create the db dir
    try:
        os.mkdir(os.environ["COLLECTIONS_PATH"] + name)
    # if it already exists
    except FileExistsError:
        print('\033[91m' + f"Error creating SDB: {name} already exists" + '\033[0m')
        return
    # then
    # also make the assets dir
    os.mkdir(os.environ["COLLECTIONS_PATH"] + name + "/assets")
    # load db prototype
    with open(os.environ["PROTOTYPE_PATH"], 'r') as f:
        prototype = json.load(f)
    # config the prototype
    prototype['name'] = name
    prototype['description'] = input(">>> SDB description (or leave blank): ")
    # and write the config.json
    with open(os.environ["COLLECTIONS_PATH"] + name + "/config.json", 'w') as write_file:
        json.dump(prototype, write_file, indent=int(4), ensure_ascii=False)
    # final notes
    print(f"SDB \"{name}\" created on " + '\033[92m' + f"{os.environ["COLLECTIONS_PATH"] + name}" + '\033[0m')
    print("to modify your SDB presets type: " + '\033[92m' + f"ker set {name}" + '\033[0m')

# https://ollama.com/blog/embedding-models
# https://chatgpt.com/share/67a8059a-0bcc-8008-9417-f96ce53298b5