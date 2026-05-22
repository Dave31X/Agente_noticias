# crear_vectorstore.py
# Construye una base vectorial ChromaDB con metadatos utiles para retrieval.

import shutil
from collections import Counter

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import NEWS_JSON, VECTORSTORE_DIR
import json


def cargar_noticias_como_documentos():
    """
    Lee datos/noticias.json y convierte cada noticia en Document.
    Usar JSON preserva fuente, fecha, categoria, tema y URL para que el agente cite mejor.
    """
    if not NEWS_JSON.exists():
        raise FileNotFoundError(
            f"No existe {NEWS_JSON}. Ejecuta primero: python3 obtener_noticias.py"
        )

    print(f"📂 Leyendo noticias desde {NEWS_JSON}...")
    with open(NEWS_JSON, "r", encoding="utf-8") as f:
        noticias = json.load(f)

    if not isinstance(noticias, list) or not noticias:
        raise ValueError("datos/noticias.json no contiene una lista de noticias.")

    documentos = []
    categorias = Counter()

    for i, noticia in enumerate(noticias, 1):
        titulo = noticia.get("titulo", "").strip()
        contenido = noticia.get("contenido") or noticia.get("descripcion") or ""
        descripcion = noticia.get("descripcion", "")

        if len((titulo + contenido).strip()) < 120:
            continue

        categoria = noticia.get("categoria") or inferir_categoria(noticia.get("tema", ""))
        categorias[categoria] += 1

        texto = "\n".join(
            [
                f"TITULO: {titulo}",
                f"FUENTE: {noticia.get('fuente', '')}",
                f"FECHA: {noticia.get('fecha', '')}",
                f"CATEGORIA: {categoria}",
                f"TEMA: {noticia.get('tema', '')}",
                f"DESCRIPCION: {descripcion}",
                f"CONTENIDO: {contenido}",
                f"URL: {noticia.get('url', '')}",
            ]
        )

        documentos.append(
            Document(
                page_content=texto,
                metadata={
                    "id_noticia": i,
                    "titulo": titulo[:240],
                    "fuente": noticia.get("fuente", ""),
                    "fecha": noticia.get("fecha", ""),
                    "categoria": categoria,
                    "tema": noticia.get("tema", ""),
                    "url": noticia.get("url", ""),
                },
            )
        )

    print(f"   ✅ {len(documentos)} noticias cargadas como documentos")
    print("   📊 Categorias:")
    for categoria, cantidad in categorias.most_common():
        print(f"      - {categoria}: {cantidad}")
    return documentos


def inferir_categoria(tema):
    tema_lower = (tema or "").lower()
    reglas = {
        "Elecciones presidenciales Colombia 2026": ["presidencial", "presidente", "elecciones 2026"],
        "Candidatos y propuestas": ["candidato", "precandidato", "propuesta", "programa"],
        "Encuestas y opinion publica": ["encuesta", "sondeo", "favorabilidad", "opinion"],
        "Partidos, coaliciones y Congreso": ["partido", "coalicion", "congreso", "senado"],
        "Instituciones y reglas electorales": ["registraduria", "cne", "calendario", "garantias"],
        "Gobierno y contexto politico": ["petro", "gobierno", "reforma", "oposicion"],
        "Seguridad y riesgos electorales": ["seguridad", "riesgo", "moe", "desinformacion"],
    }
    for categoria, claves in reglas.items():
        if any(clave in tema_lower for clave in claves):
            return categoria
    return "Politica Colombia"


def crear_chunks(documentos):
    """
    Chunks medianos: suficiente contexto para noticias, con solape para no cortar ideas.
    """
    print("\n✂️  Dividiendo documentos en chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documentos)
    print(f"   ✅ {len(chunks)} chunks creados")
    return chunks


def crear_vectorstore(chunks):
    print("\n🔢 Creando embeddings con all-MiniLM-L6-v2...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    if VECTORSTORE_DIR.exists():
        print(f"🧹 Reconstruyendo base existente en {VECTORSTORE_DIR}...")
        shutil.rmtree(VECTORSTORE_DIR)

    print("💾 Guardando en ChromaDB...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTORSTORE_DIR),
    )

    print(f"   ✅ Vector store creado con {len(chunks)} fragmentos")
    print(f"   📁 Guardado en: {VECTORSTORE_DIR}")
    return vectorstore


if __name__ == "__main__":
    print("🚀 Creando Vector Store focalizado en politica colombiana...\n")
    documentos = cargar_noticias_como_documentos()
    chunks = crear_chunks(documentos)
    vectorstore = crear_vectorstore(chunks)

    print("\n🧪 Prueba de busqueda:")
    resultados = vectorstore.similarity_search("elecciones presidenciales Colombia candidatos encuestas", k=3)
    for r in resultados:
        meta = r.metadata
        print(f"   → {meta.get('fecha')} | {meta.get('fuente')} | {meta.get('titulo', '')[:90]}...")

    print("\n🎉 Vector Store listo!")
