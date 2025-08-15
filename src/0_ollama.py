# reference: https://github.com/ollama/ollama/blob/main/docs/turbo.md#ollamas-cli
import os
from dotenv import load_dotenv
from ollama import Client

load_dotenv()

client = Client(
    host="https://ollama.com",
    headers={'Authorization': os.environ["OLLAMA_API_KEY"]}
)

messages = [
  {
    'role': 'user',
    'content': 'Why is the sky blue?',
  },
]

for part in client.chat('gpt-oss:20b', messages=messages, stream=True):
    print(part['message']['content'], end='', flush=True)

