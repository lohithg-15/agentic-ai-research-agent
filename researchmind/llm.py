"""
llm.py — Direct Gemini API Wrapper

No LangChain. No frameworks. Just google-genai SDK (new official package).
Provides a single async function to call Gemini for all agents.
Includes a global rate limiter to stay within free-tier quotas.
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

# ── Rate Limiter ─────────────────────────────────────────────
# Free tier allows ~15 requests/minute. We space calls ~5s apart
# and use a semaphore so at most 2 calls run at once.
_semaphore = asyncio.Semaphore(2)
_MIN_DELAY = 4  # seconds between calls


async def call_gemini(
    prompt: str,
    system_instruction: str = "",
    temperature: float = 0.7,
    model_name: str = DEFAULT_MODEL,
    max_retries: int = 5,
) -> str:
    """
    Call the Gemini API with a prompt and return the text response.

    Includes rate limiting (semaphore + delay) and exponential backoff
    on 429 / RESOURCE_EXHAUSTED errors.
    """
    if not _client:
        raise RuntimeError("No GEMINI_API_KEY found. Set it in .env file.")

    # Build config
    config = genai.types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction if system_instruction else None,
    )

    # Acquire semaphore so at most 2 calls happen concurrently
    async with _semaphore:
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
                    # Small delay after success to stay within rate limits
                    await asyncio.sleep(_MIN_DELAY)
                    return response.text.strip()
                else:
                    return "[No response from Gemini]"

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Longer wait for rate limit errors
                if "429" in str(e) or "resource_exhausted" in error_str or "quota" in error_str:
                    wait_time = 10 * (attempt + 1)  # 10s, 20s, 30s, 40s, 50s
                    print(f"  Rate limited (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s...")
                else:
                    wait_time = 3 ** attempt  # 1s, 3s, 9s, 27s
                    print(f"  Gemini API error (attempt {attempt + 1}/{max_retries}): {e}")

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
