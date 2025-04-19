import sys
from enum import Enum
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI(
    base_url="http://0.0.0.0:8000/v1",
    api_key="-"
)

stream = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",
    messages=[
        {"role": "user", "content": "How do you suggest navigating the tough job market in software engineering?"},
    ],
    max_tokens=10,
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        sys.stdout.write(chunk.choices[0].delta.content)
        sys.stdout.flush()
