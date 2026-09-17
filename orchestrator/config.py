import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage
from core.config import settings

google_api_key = settings.gemini_api_key
gemini_model_name = settings.default_gemini_model

primary_llm = ChatGoogleGenerativeAI(
    model=gemini_model_name,
    google_api_key=google_api_key,
    temperature=0.1
) if google_api_key else None

llm = primary_llm


def invoke_llm_with_fallback(messages, response_format=None):
    """Gemini-only invocation; retain the public API and rate-limit retry."""
    if primary_llm:
        for attempt in range(2):
            try:
                model = primary_llm
                if response_format and response_format.get("type") == "json_object":
                    model = model.bind(response_mime_type="application/json")
                return model.invoke(messages)
            except Exception as err:
                if "429" in str(err) and attempt == 0:
                    print("   [!] Gemini Rate Limited. Pausing 10s before retry...")
                    time.sleep(10)
                else:
                    print(f"   [!] Gemini ({gemini_model_name}) failed: {err}")
                    break

    print("[Critical] Gemini unavailable; no other LLM provider is enabled.")
    if response_format and response_format.get("type") == "json_object":
        return AIMessage(content="{}")
    return AIMessage(content="")
