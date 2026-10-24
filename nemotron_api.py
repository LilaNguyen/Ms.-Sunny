"""Small, lazy-initialized client for the NVIDIA OpenAI-compatible API.

Importing this module does not require a configured API key. This lets the
Flask app start locally and lets the agent's rule-based fallback handle
requests when the model is unavailable.
"""
import os
from openai import OpenAI

BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = "nvidia/nemotron-nano-9b-v2"

_client = None
_client_api_key = None


def get_client() -> OpenAI:
    """Return a cached client, reading credentials when the first call is made."""
    global _client, _client_api_key
    api_key = os.environ.get("NVIDIA_API_KEY") or os.environ.get("NEMOTRON_API_KEY")
    if not api_key:
        raise ValueError(
            "NVIDIA_API_KEY (or NEMOTRON_API_KEY) is not set. "
            "Configure it in your environment or Replit Secrets to enable Nemotron."
        )
    if _client is None or _client_api_key != api_key:
        _client = OpenAI(base_url=BASE_URL, api_key=api_key)
        _client_api_key = api_key
    return _client


def call_nemotron(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
) -> str:
    """Send a chat completion request and return its text response."""
    completion = get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        top_p=0.9,
        max_tokens=512,
    )
    message = completion.choices[0].message.content
    if not message:
        raise RuntimeError("Nemotron returned an empty response.")
    return message.strip()
