from openai import OpenAI
import ollama

# instance openAI client
client = OpenAI()

# available providers
available_providers = ["OpenAI", "Ollama"]


# general function to chat
def chat (provider: str, model: str, prompt: str):
  # if provider was not found
  if provider not in available_providers:
    raise ValueError(f"{privider} not available, only: {available_providers}")

  #
  if provider == "OpenAI":
    # chat with OpenAI
    completion = client.chat.completions.create(
      model=model,
      messages=[
        {"role": "user","content": prompt}
      ]
    )
    # and return message
    return completion.choices[0].message.content

  # 
  if provider == "Ollama"
    response = ollama.chat(
      model=model,
      messages=[
        {"role": "user", "content": prompt}
      ]
    )
    return response['message']['content']