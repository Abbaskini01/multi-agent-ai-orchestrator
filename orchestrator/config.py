import os
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
google_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Tier 1: Primary Model (Groq 70B)
primary_llm = ChatGroq(
    temperature=0.1,
    model_name="llama-3.3-70b-versatile",
    groq_api_key=groq_api_key
)

# Tier 2: Gemini 2.0 Flash
fallback_gemini = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=google_api_key,
    temperature=0.1
) if google_api_key else None

# Tier 3: Lightweight Backup (Groq 8B - Separate Quota)
fallback_groq_8b = ChatGroq(
    temperature=0.1,
    model_name="llama-3.1-8b-instant",
    groq_api_key=groq_api_key
) if groq_api_key else None

llm = primary_llm


def invoke_llm_with_fallback(messages, response_format=None):
    """
    3-Tier Resilience Engine:
    Tier 1: Groq Llama 3.3 70B
    Tier 2: Gemini 2.0 Flash (with auto-sleep retry on 429)
    Tier 3: Groq Llama 3.1 8B Instant
    """
    # --- Try Tier 1: Primary Groq 70B ---
    try:
        model = primary_llm
        if response_format:
            model = model.bind(response_format=response_format)
        return model.invoke(messages)
    except Exception as e1:
        print(f"\n[⚠️ Multi-Model Routing] Primary Groq 70B unavailable: {e1}")

    # --- Try Tier 2: Gemini 2.0 Flash ---
    if fallback_gemini:
        print("-> Failing over to Tier 2: Gemini 2.0 Flash...")
        for attempt in range(2):
            try:
                model = fallback_gemini
                if response_format:
                    model = model.bind(response_format=response_format)
                return model.invoke(messages)
            except Exception as e2:
                if "429" in str(e2) and attempt == 0:
                    print("   [!] Gemini Rate Limited. Pausing 10s before retry...")
                    time.sleep(10)
                else:
                    print(f"   [!] Tier 2 Gemini failed: {e2}")
                    break

    # --- Try Tier 3: Groq 8B Instant ---
    if fallback_groq_8b:
        print("-> Failing over to Tier 3: Groq Llama 3.1 8B Instant...")
        try:
            model = fallback_groq_8b
            if response_format:
                model = model.bind(response_format=response_format)
            return model.invoke(messages)
        except Exception as e3:
            print(f"   [!] Tier 3 Groq 8B failed: {e3}")

    print("[❌ Critical] All LLM providers are currently rate-limited.")
    if response_format and response_format.get("type") == "json_object":
        return AIMessage(content="{}")
    return AIMessage(content="")