import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
google_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Primary Engine: Groq Llama 3.3 70B
primary_llm = ChatGroq(
    temperature=0.1,
    model_name="llama-3.3-70b-versatile",
    groq_api_key=groq_api_key
)

# Alias to ensure backwards compatibility with legacy imports
llm = primary_llm

# Secondary Fallback Engine: Google Gemini 2.5 Flash (or Groq Llama 3.1 8B backup)
if google_api_key:
    fallback_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key,
        temperature=0.1
    )
else:
    fallback_llm = ChatGroq(
        temperature=0.1,
        model_name="llama-3.1-8b-instant",
        groq_api_key=groq_api_key
    )


def invoke_llm_with_fallback(messages, response_format=None):
    """
    Phase 10 Multi-Model Routing Engine:
    Tries Primary LLM (Groq Llama 3.3 70B).
    On rate-limit or API error, seamlessly fails over to Fallback LLM.
    """
    try:
        model = primary_llm
        if response_format:
            model = model.bind(response_format=response_format)
        return model.invoke(messages)
    except Exception as primary_err:
        print(f"\n[⚠️ Multi-Model Routing Triggered] Primary LLM Error: {primary_err}")
        print("-> Failing over to Secondary Fallback Engine...")
        model = fallback_llm
        if response_format:
            model = model.bind(response_format=response_format)
        return model.invoke(messages)