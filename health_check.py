"""Chequeo rapido del estado local de NewsAgent."""

import json
import os

from dotenv import load_dotenv

from config import CORPUS_METADATA, NEWS_JSON, NEWS_TXT, VECTORSTORE_DIR


def estado(ok, mensaje):
    icono = "OK " if ok else "WARN "
    print(f"{icono}{mensaje}")
    return ok


def contar_noticias():
    if not NEWS_JSON.exists():
        return 0
    try:
        with open(NEWS_JSON, "r", encoding="utf-8") as archivo:
            data = json.load(archivo)
        return len(data) if isinstance(data, list) else 0
    except Exception:
        return 0


def main():
    load_dotenv()
    print("NewsAgent health check")
    print("=" * 56)

    noticias = contar_noticias()
    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    newsapi_ok = bool(os.getenv("NEWS_API_KEY"))
    if provider == "gemini":
        llm_ok = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
        llm_msg = "Gemini configurado (GOOGLE_API_KEY o GEMINI_API_KEY)"
    elif provider == "groq":
        llm_ok = bool(os.getenv("GROQ_API_KEY"))
        llm_msg = "Groq configurado (GROQ_API_KEY)"
    else:
        llm_ok = False
        llm_msg = f"Proveedor LLM no soportado: {provider}"

    required_checks = [
        estado(llm_ok, llm_msg),
        estado(NEWS_JSON.exists() and noticias > 0, f"Corpus JSON disponible ({noticias} noticias)"),
        estado(NEWS_TXT.exists() and NEWS_TXT.stat().st_size > 0, "Corpus TXT disponible"),
        estado(CORPUS_METADATA.exists(), "Metadata del corpus disponible"),
        estado(VECTORSTORE_DIR.exists() and any(VECTORSTORE_DIR.iterdir()), "Vectorstore Chroma disponible"),
    ]
    estado(newsapi_ok, "NEWS_API_KEY configurada; si falta, ingesta usa RSS fallback")

    print("=" * 56)
    if all(required_checks):
        print("Listo: el proyecto parece preparado para Streamlit y evaluacion.")
    else:
        print("Pendiente: revisa los WARN. Flujo sugerido:")
        print("python3 obtener_noticias.py")
        print("python3 crear_vectorstore.py")
        print("streamlit run app.py")


if __name__ == "__main__":
    main()
