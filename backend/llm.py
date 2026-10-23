import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
_model = os.getenv("GEMINI_MODEL")


def generate(prompt: str) -> str:
    return _client.models.generate_content(model=_model, contents=prompt).text