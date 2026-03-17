import os
from openai import OpenAI

API_KEY = os.environ.get("NVIDIA_API_KEY") or os.environ.get("NEMOTRON_API_KEY")
BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = "nvidia/nemotron-nano-9b-v2"

if not API_KEY:
    raise ValueError("NVIDIA_API_KEY is not set in Replit secrets!")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


def call_nemotron(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        top_p=0.9,
        max_tokens=512,
    )
    return completion.choices[0].message.content.strip()
