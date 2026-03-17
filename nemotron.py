import os
from openai import OpenAI

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
NEMOTRON_MODEL = "nvidia/nemotron-nano-9b-v2"

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not NVIDIA_API_KEY:
            raise ValueError(
                "NVIDIA_API_KEY environment variable is not set. "
                "Please set it to use the NVIDIA Nemotron model."
            )
        _client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=NVIDIA_API_KEY,
        )
    return _client


def call_nemotron(system_prompt: str, user_prompt: str, temperature: float = 0.6) -> str:
    client = get_client()
    completion = client.chat.completions.create(
        model=NEMOTRON_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=512,
    )
    return completion.choices[0].message.content.strip()
