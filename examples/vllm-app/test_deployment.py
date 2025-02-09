from enum import Enum
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI(
    base_url="http://0.0.0.0:8000/v1",
    api_key="-"
)

completions = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",
    messages=[
        {"role": "user", "content": "Classify this sentiment: vLLM is wonderful!"}
    ],
    extra_body={"guided_choice": ["positive", "negative"]},
)
print(completions.choices[0])
