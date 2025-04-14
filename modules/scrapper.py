import os
import importlib
from modules.extras import generate_id_and_source


# function to list available files in scrappers
def available_extensions ():
    available = []
    # iterate files in scrappers
    for file in os.listdir(os.environ["PROJECT_PATH"] + "/modules/scrappers"):
        # every file that ends in .py
        if file.endswith(".py"):
            # get the filename without the .py
            file_name = os.path.splitext(file)[0]
            # and save it
            available.append(file_name)
    # return results
    return available

# function to get content from files
def get_content (path, current_dir, collection):
    # get the file extension
    extension = path.split('.')[-1]
    # make it lowercase
    extension = extension.lower()
    # copy the file to assets
    new_path = os.environ["COLLECTIONS_PATH"] + f"{collection}/assets/{path.split('/')[-1]}.{extension}"

##############################################################

    if extension in available_extensions():
        # then import the content scrapper
        scrapper = importlib.import_module(f"modules.scrappers.{extension}")
        # use it to analyze the file
        content = scrapper.analyze(path)
        # add the ids and source to the file
        content = generate_id_and_source(content, path)

##############################################################

    # if other extension
    else:
        raise ValueError(f"Only accepted {', '.join(available_extensions())} files")

    # if other file was accepted
    print(f"found {len(content)} items in {path}")

    return content, new_path