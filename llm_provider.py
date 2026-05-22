"""Factory central para elegir proveedor LLM desde variables de entorno."""

import os

from dotenv import load_dotenv

load_dotenv(override=True)


def _int_env(nombre: str, default: int) -> int:
    try:
        return int(os.getenv(nombre, str(default)))
    except Exception:
        return default


def crear_llm(temperature: float = 0.25, max_tokens: int | None = None):
    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        modelo = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        salida_maxima = max_tokens if max_tokens is not None else _int_env("GEMINI_MAX_TOKENS", 768)
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        return ChatGoogleGenerativeAI(
            model=modelo,
            temperature=temperature,
            max_output_tokens=salida_maxima,
            max_retries=2,
            google_api_key=api_key,
        )

    if provider == "groq":
        from langchain_groq import ChatGroq

        modelo = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        salida_maxima = max_tokens if max_tokens is not None else _int_env("GROQ_MAX_TOKENS", 512)
        return ChatGroq(
            model=modelo,
            temperature=temperature,
            max_tokens=salida_maxima,
        )

    raise ValueError(
        f"Proveedor LLM no soportado: {provider}. Usa LLM_PROVIDER=gemini o LLM_PROVIDER=groq."
    )


def descripcion_llm() -> str:
    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    if provider == "gemini":
        return f"Gemini · {os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')}"
    if provider == "groq":
        return f"Groq · {os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')}"
    return provider
