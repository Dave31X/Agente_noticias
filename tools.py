# 3_tools.py
# Define todas las herramientas que el agente puede usar

from langchain.tools import tool
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from datetime import datetime
import json
import os

# Cargar el vector store que ya creamos
from langchain_community.embeddings import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

vectorstore = Chroma(
    persist_directory="./datos/noticias_db",
    embedding_function=embeddings
)

# ── TOOL 1: Buscar noticias (RAG) ─────────────────────────────
@tool
def buscar_noticias(consulta: str) -> str:
    """
    Busca noticias relevantes en la base de datos sobre politica colombiana,
    elecciones presidenciales, candidatos, encuestas y contexto electoral.
    Usala cuando el usuario pregunte sobre noticias, eventos o temas de actualidad.
    """
    resultados = vectorstore.similarity_search(consulta, k=6)
    
    if not resultados:
        return "No encontré noticias relevantes sobre ese tema."
    
    respuesta = f"Encontré {len(resultados)} noticias relevantes:\n\n"
    for i, doc in enumerate(resultados, 1):
        respuesta += f"--- Noticia {i} ---\n"
        respuesta += f"{doc.page_content[:400]}\n\n"
    
    return respuesta

# ── TOOL 2: Clasificar el tema de una consulta ────────────────
@tool
def clasificar_tema(consulta: str) -> str:
    """
    Clasifica a qué categoría pertenece una consulta o noticia.
    Útil para entender de qué área trata la pregunta del usuario.
    """
    consulta_lower = consulta.lower()
    
    # Cambia esta sección en clasificar_tema
    categorias = {
    "Elecciones presidenciales": ["presidencial", "presidenciales", "candidato",
                                  "candidata", "campaña", "voto", "encuesta"],
    "Política Colombia": ["presidente", "gobierno", "congreso", "elección",
                          "senado", "ministro", "partido", "votación",
                          "petro", "oposición", "coalición"],
    "Economía": ["inflación", "dólar", "economía", "pib", "desempleo",
                 "banco", "finanzas", "mercado", "precio"],
    "Tecnología": ["inteligencia artificial", "tecnología",
                   "software", "startup", "digital", "meta", "google", "apple"],
    "Deportes": ["fútbol", "mundial", "liga", "equipo", "jugador",
                 "gol", "selección", "hincha"],
    "Salud": ["salud", "hospital", "enfermedad", "vacuna",
              "médico", "pandemia", "virus"]
    }
    
    for categoria, palabras_clave in categorias.items():
        if any(palabra in consulta_lower for palabra in palabras_clave):
            return f"Categoría identificada: {categoria}"
    
    return "Categoría: General / Actualidad"

# ── TOOL 3: Obtener fecha y contexto temporal ─────────────────
@tool
def obtener_contexto_temporal(input: str = "") -> str:
    """
    Retorna la fecha actual y el contexto temporal.
    Úsala cuando necesites saber qué día es hoy o contextualizar las noticias.
    """
    ahora = datetime.now()
    return (
        f"Fecha actual: {ahora.strftime('%A %d de %B de %Y')}\n"
        f"Hora: {ahora.strftime('%H:%M')}\n"
        f"El enfoque configurado busca noticias de los últimos 30 días."
    )

# ── TOOL 4: Contar y resumir noticias disponibles ─────────────
@tool  
def estadisticas_noticias(input: str = "") -> str:
    """
    Muestra cuántas noticias hay disponibles en la base de datos
    y de qué temas son. Úsala cuando el usuario pregunte qué información tienes.
    """
    try:
        with open("datos/noticias.json", "r", encoding="utf-8") as f:
            noticias = json.load(f)
        
        total = len(noticias)
        temas = {}
        for n in noticias:
            tema = n.get("tema", "General")
            temas[tema] = temas.get(tema, 0) + 1
        
        resumen = f"📊 Base de datos de noticias:\n"
        resumen += f"   Total de noticias: {total}\n"
        resumen += f"   Distribución por tema:\n"
        for tema, cantidad in temas.items():
            resumen += f"   - {tema}: {cantidad} noticias\n"
        
        return resumen
    except:
        return "No se pudo obtener estadísticas de las noticias."
