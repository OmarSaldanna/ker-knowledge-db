# import ollama

# # generate a response combining the prompt and data we retrieved in step 2
# # note: this function still doesn't have context storage
# def chat (model: str, prompt: str):
#   # the function to return the message as a data flow
#   def stream_generator():
#     # make the prompt
#     stream = ollama.chat(
#       model=model,
#       messages=[
#         {"role": "user", "content": prompt}
#       ],
#       # as a stream
#       stream=True
#     )
#     # and the answer
#     for ans in stream:
#       yield ans["message"]["content"]
#   # return the function
#   return stream_generator()


from openai import OpenAI

client = OpenAI()

def chat(model: str, prompt: str):
  # 
  completion = client.chat.completions.create(
    model=model,
    messages=[
      {
        "role": "user",
        "content": prompt
      }
    ]
  )

  return completion.choices[0].message.content