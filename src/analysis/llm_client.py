"""
Shared Gemini client using the new google-genai SDK.

Used by:
    - resume_structurer.py
    - ideal_profile_generator.py

Requirements:
    pip install google-genai python-dotenv

Create a .env file:

    GEMINI_API_KEY=your_api_key_here
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env
load_dotenv()

# Use a currently supported model
MODEL_NAME = "gemini-3.6-flash"

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Create the Gemini client once."""

    global _client

    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not found.\n"
                "Create a .env file containing:\n"
                "GEMINI_API_KEY=YOUR_API_KEY"
            )

        _client = genai.Client(api_key=api_key)

    return _client


def generate_structured_json(
    prompt: str,
    response_schema: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate structured JSON using Gemini.

    Args:
        prompt: Prompt to send to Gemini.
        response_schema: JSON Schema describing the expected response.

    Returns:
        Parsed Python dictionary.
    """

    client = _get_client()

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
                response_json_schema=response_schema,
            ),
        )

    except Exception as e:
        raise RuntimeError(f"Gemini API call failed:\n{e}") from e

    # New SDK sometimes parses JSON automatically
    if getattr(response, "parsed", None) is not None:
        return response.parsed

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    try:
        return json.loads(response.text)

    except json.JSONDecodeError as e:
        raise RuntimeError(
            "Gemini returned invalid JSON:\n\n"
            f"{response.text}"
        ) from e


if __name__ == "__main__":

    test_schema = {
        "type": "object",
        "properties": {
            "skills": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            }
        },
        "required": ["skills"]
    }

    result = generate_structured_json(
        prompt="List three skills every Python backend developer should have. Return JSON only.",
        response_schema=test_schema,
    )

    print(json.dumps(result, indent=4))
