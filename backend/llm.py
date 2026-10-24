import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
_model = os.getenv("GEMINI_MODEL")


_provider = (os.getenv("LLM_PROVIDER") or "gemini").strip().lower()
_bedrock = None


def _gemini(prompt: str) -> str:
    return _client.models.generate_content(model=_model, contents=prompt).text


def _bedrock_generate(prompt: str) -> str:
    global _bedrock
    if _bedrock is None:
        import boto3
        _bedrock = boto3.client("bedrock-runtime", region_name=os.environ["AWS_DEFAULT_REGION"])
    r = _bedrock.converse(
        modelId=os.environ["BEDROCK_MODEL_ID"],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 600},
    )
    return r["output"]["message"]["content"][0]["text"]


def generate(prompt: str) -> str:
    if _provider == "bedrock":
        try:
            return _bedrock_generate(prompt)
        except Exception as e:
            print("llm: bedrock failed (" + type(e).__name__ + "), falling back to gemini")
    return _gemini(prompt)