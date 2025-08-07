# from openai import OpenAI

# client = OpenAI()

# def make_embeddings (model: str, text: str) -> list:
#     # make the embeddings
#     respuesta = client.embeddings.create(
#         input=text,
#         model=model
#     )
#     # return the embeddings and the usage
#     return respuesta.data[0].embedding# , respuesta["usage"]


import ollama

def make_embeddings (model: str, text: str) -> list:
    response = ollama.embeddings(
        model=model,
        prompt=text
    )
    return response['embedding']