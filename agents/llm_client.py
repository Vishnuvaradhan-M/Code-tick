# agents/llm_client.py
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def call_llm(prompt: str) -> str:
    """
    Single shared LLM entry point.
    Takes one prompt string. Returns LLM response string.
    All agents call this with a single formatted prompt.
    """
    response = _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an expert SRE incident analyst. Always respond with valid JSON only. No markdown, no explanation, no code blocks. Just the raw JSON object."
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        temperature=0.1,
        max_tokens=1500,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    result = call_llm('Return this exact JSON: {"status": "ok", "model": "llama-3.3-70b-versatile"}')
    print("LLM test:", result)