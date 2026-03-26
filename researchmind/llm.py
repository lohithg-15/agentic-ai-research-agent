"""
llm.py — Direct Gemini API Wrapper

No LangChain. No frameworks. Just google-genai SDK (new official package).
Provides a single async function to call Gemini for all agents.
"""

import os
import asyncio
from google import genai
from dotenv import load_dotenv

# ── Load API Key ──────────────────────────────────────────────
load_dotenv()
_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Create the client with the API key
_client = genai.Client(api_key=_API_KEY) if _API_KEY else None

# ── Default Model ────────────────────────────────────────────
DEFAULT_MODEL = "gemini-2.0-flash"


async def call_gemini(
    prompt: str,
    system_instruction: str = "",
    temperature: float = 0.7,
    model_name: str = DEFAULT_MODEL,
    max_retries: int = 3,
) -> str:
    """
    Call the Gemini API with a prompt and return the text response.

    Args:
        prompt: The user prompt to send.
        system_instruction: Optional system-level instruction for the model.
        temperature: Creativity control (0.0 = deterministic, 1.0 = creative).
        model_name: Which Gemini model to use.
        max_retries: Number of retries with exponential backoff.

    Returns:
        The model's text response.
    """
    if not _client:
        raise RuntimeError("No GEMINI_API_KEY found. Set it in .env file.")

    # Build config
    config = genai.types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction if system_instruction else None,
    )

    # Retry loop with exponential backoff
    last_error = None
    for attempt in range(max_retries):
        try:
            # Run the synchronous SDK call in a thread pool
            response = await asyncio.to_thread(
                _client.models.generate_content,
                model=model_name,
                contents=prompt,
                config=config,
            )
            # Extract text
            if response and response.text:
                return response.text.strip()
            else:
                return "[No response from Gemini]"

        except Exception as e:
            last_error = e
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            print(f"  ⚠ Gemini API error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)

    raise RuntimeError(f"Gemini API failed after {max_retries} attempts: {last_error}")


async def call_gemini_json(
    prompt: str,
    system_instruction: str = "",
    temperature: float = 0.3,
) -> str:
    """
    Call Gemini expecting a JSON response.
    Uses lower temperature for more structured output.
    """
    json_instruction = (
        system_instruction
        + "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation, just JSON."
    )
    return await call_gemini(
        prompt=prompt,
        system_instruction=json_instruction,
        temperature=temperature,
    )
