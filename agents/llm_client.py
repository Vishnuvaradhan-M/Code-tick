# agents/llm_client.py
# Shared LLM client using Groq — free, fast, stable
# All 4 agents import call_llm from here
# Never call Groq directly from agent files

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Single client instance shared by all agents
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Model: llama3-70b — best reasoning, completely free
MODEL = "llama-3.3-70b-versatile"

def call_llm(prompt: str, max_tokens: int = 1500) -> str:
    """
    Single function all 4 agents use
    Returns raw text string from LLM
    Raises exception if call fails
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Always respond with valid JSON only. No markdown, no code blocks, no extra text."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=max_tokens,
        temperature=0.1
    )
    return response.choices[0].message.content.strip()


# Test block
if __name__ == "__main__":
    print("Testing Groq connection...")
    print("-" * 40)

    try:
        result = call_llm('Return this JSON: {"status": "working", "model": "llama3"}')
        print("Response:", result)
        print("\n✅ Groq API working correctly")
        print("   Ready to build agents")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Check GROQ_API_KEY in .env file")