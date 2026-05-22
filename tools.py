# tools.py
# Herramientas del agente: retrieval, cobertura, clasificacion y contexto temporal.

import json
import os
from collections import Counter
from datetime import datetime
from urllib.parse import urlparse

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from config import (
    CORPUS_METADATA,
    DIAS_BUSQUEDA,
    ENFOQUE_AGENTE,
    NEWS_JSON,
    PALABRAS_COLOMBIA,
    PALABRAS_POLITICA_ELECTORAL,
    VECTORSTORE_DIR,
)

load_dotenv(override=True)

_embeddings = None
_vectorstore = None
DOMINIOS_WEB_PRIORITARIOS = [
    "eltiempo.com",
    "elespectador.com",
    "semana.com",
    "caracol.com.co",
    "lafm.com.co",
    "bluradio.com",
    "infobae.com",
    "cambio.com.co",
    "elpais.com.co",
    "registraduria.gov.co",
    "cne.gov.co",
]
PALABRAS_ENFOQUE_WEB = [
    "elecciones",
    "presidencial",
    "presidenciales",
    "candidato",
    "candidatos",
    "encuesta",
    "encuestas",
    "voto",
    "politica",
    "política",
    "gobierno",
    "congreso",
    "petro",
    "registraduria",
    "registraduría",
    "cne",
]
PALABRAS_CONSULTA_HISTORICA_WEB = [
    "vicepresidencial",
    "vicepresidente",
    "vicepresidenta",
    "formula",
    "fórmula",
    "lista completa",
    "inscritos",
    "cierre de inscripciones",
]


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


def _get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        if not VECTORSTORE_DIR.exists():
            raise FileNotFoundError(
                "No existe datos/noticias_db. Ejecuta python3 crear_vectorstore.py despues de obtener noticias."
            )
        _vectorstore = Chroma(
            persist_directory=str(VECTORSTORE_DIR),
            embedding_function=_get_embeddings(),
        )
    return _vectorstore


def _cargar_noticias():
    if not NEWS_JSON.exists():
        return []
    with open(NEWS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _recortar(texto, limite=360):
    texto = " ".join((texto or "").split())
    return texto[:limite].rstrip() + ("..." if len(texto) > limite else "")


def _dominio(url):
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return "Sin fuente"


def _score_enfoque(noticia):
    texto = " ".join(
        [
            noticia.get("titulo", ""),
            noticia.get("descripcion", ""),
            noticia.get("contenido", ""),
            noticia.get("tema", ""),
            noticia.get("categoria", ""),
        ]
    ).lower()
    colombia = sum(1 for p in PALABRAS_COLOMBIA if p in texto)
    politica = sum(1 for p in PALABRAS_POLITICA_ELECTORAL if p in texto)
    if colombia == 0 or politica == 0:
        return 0
    return colombia * 2 + politica


@tool
def buscar_noticias(consulta: str) -> str:
    """
    Busca noticias relevantes en ChromaDB sobre politica colombiana, elecciones 2026,
    candidatos, encuestas, partidos, instituciones y riesgos electorales.
    Usala antes de responder preguntas factuales o de actualidad.
    """
    try:
        vectorstore = _get_vectorstore()
        resultados_crudos = vectorstore.similarity_search_with_score(consulta, k=10)
    except Exception as error:
        return f"No pude consultar la base vectorial: {error}"

    resultados = []
    vistos = set()
    for doc, score in resultados_crudos:
        meta = doc.metadata or {}
        clave = (
            meta.get("url")
            or meta.get("titulo")
            or _recortar(doc.page_content, 120)
        )
        if clave in vistos:
            continue
        vistos.add(clave)
        resultados.append((doc, score))
        if len(resultados) >= 6:
            break

    if not resultados:
        return "No encontre noticias relevantes sobre ese tema en la base local."

    respuesta = [f"Consulta: {consulta}", f"Resultados recuperados: {len(resultados)}"]
    for i, (doc, score) in enumerate(resultados, 1):
        meta = doc.metadata or {}
        respuesta.extend(
            [
                f"\n--- Resultado {i} ---",
                f"Titulo: {meta.get('titulo', 'Sin titulo')}",
                f"Fuente: {meta.get('fuente', 'Sin fuente')}",
                f"Fecha: {meta.get('fecha', 'Sin fecha')}",
                f"Categoria: {meta.get('categoria', 'Sin categoria')}",
                f"Tema: {meta.get('tema', 'Sin tema')}",
                f"Distancia semantica: {score:.4f}",
                f"Fragmento: {_recortar(doc.page_content)}",
            ]
        )
    return "\n".join(respuesta)


@tool
def buscar_web_noticias(consulta: str) -> str:
    """
    Investiga noticias recientes en la web usando Tavily Search.
    Usala cuando el corpus local no tenga evidencia suficiente, este desactualizado
    o el usuario pida informacion muy reciente. No reemplaza el retrieval local:
    complementa la respuesta y debe citar titulo, fuente y fecha.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return (
            "La busqueda web con Tavily no esta configurada. "
            "Agrega TAVILY_API_KEY en tu archivo .env y reinstala dependencias si hace falta: "
            "pip install tavily-python"
        )

    query = consulta.strip()
    if "colombia" not in query.lower():
        query = f"{query} Colombia"
    if not any(palabra in query.lower() for palabra in PALABRAS_ENFOQUE_WEB):
        query = f"{query} politica actualidad"
    ventana_dias = 120 if any(palabra in query.lower() for palabra in PALABRAS_CONSULTA_HISTORICA_WEB) else DIAS_BUSQUEDA

    try:
        from tavily import TavilyClient

        cliente = TavilyClient(api_key=api_key)
        parametros = {
            "query": query,
            "search_depth": "basic",
            "topic": "general",
            "country": "colombia",
            "days": ventana_dias,
            "max_results": 5,
            "include_answer": False,
            "include_raw_content": ventana_dias != DIAS_BUSQUEDA,
            "include_usage": True,
        }
        if ventana_dias == DIAS_BUSQUEDA and any(palabra in query.lower() for palabra in PALABRAS_ENFOQUE_WEB):
            parametros["include_domains"] = DOMINIOS_WEB_PRIORITARIOS

        respuesta = cliente.search(
            **parametros
        )
    except Exception as error:
        return f"No pude investigar en la web con Tavily en este momento: {error}"

    resultados = []
    for item in respuesta.get("results", []):
        titulo = (item.get("title") or "").strip()
        enlace = (item.get("url") or "").strip()
        contenido = (item.get("content") or "").strip()
        raw_content = (item.get("raw_content") or item.get("rawContent") or "").strip()
        fecha = item.get("published_date") or item.get("publishedDate") or ""
        score = item.get("score")

        if not titulo and not enlace:
            continue

        resultados.append(
            {
                "titulo": titulo or "Sin titulo",
                "fuente": _dominio(enlace),
                "fecha": fecha,
                "url": enlace,
                "contenido": raw_content or contenido,
                "score": score,
            }
        )

    if not resultados:
        return "Tavily no encontro resultados web recientes para esa consulta."

    lineas = [
        f"Consulta web: {query}",
        "Proveedor de busqueda web: Tavily Search",
            f"Resultados web recuperados: {len(resultados[:5])}",
        f"Ventana web solicitada: ultimos {ventana_dias} dias",
    ]
    if respuesta.get("usage"):
        lineas.append(f"Uso Tavily reportado: {respuesta.get('usage')}")
    for indice, resultado in enumerate(resultados[:5], 1):
        score = resultado["score"]
        score_texto = f"{score:.4f}" if isinstance(score, (float, int)) else "Sin score"
        lineas.extend(
            [
                f"\n--- Resultado web {indice} ---",
                f"Titulo: {resultado['titulo']}",
                f"Fuente: {resultado['fuente']}",
                f"Fecha: {resultado['fecha'] or 'Sin fecha'}",
                f"Score Tavily: {score_texto}",
                f"Resumen: {_recortar(resultado['contenido'], 320)}",
            ]
        )

    return "\n".join(lineas)


@tool
def clasificar_tema(consulta: str) -> str:
    """
    Clasifica la consulta segun el enfoque del agente y detecta si esta fuera de alcance.
    """
    consulta_lower = consulta.lower()
    categorias = {
        "Elecciones presidenciales": [
            "presidencial",
            "presidenciales",
            "candidato",
            "candidata",
            "campaña",
            "voto",
            "encuesta",
        ],
        "Gobierno y contexto politico": [
            "presidente",
            "gobierno",
            "petro",
            "ministro",
            "reforma",
            "oposicion",
            "oposición",
        ],
        "Partidos, coaliciones y Congreso": [
            "congreso",
            "senado",
            "partido",
            "coalicion",
            "coalición",
            "alianza",
        ],
        "Instituciones y reglas electorales": [
            "registraduria",
            "registraduría",
            "cne",
            "calendario electoral",
            "garantias",
            "garantías",
        ],
        "Seguridad y riesgos electorales": [
            "seguridad",
            "riesgo",
            "moe",
            "violencia",
            "desinformacion",
            "desinformación",
            "delitos electorales",
        ],
    }

    for categoria, palabras_clave in categorias.items():
        if any(palabra in consulta_lower for palabra in palabras_clave):
            return f"Categoria identificada: {categoria}. Esta dentro del enfoque del agente."

    if any(p in consulta_lower for p in ["colombia", "petro", "bogota", "bogotá"]):
        return "Categoria identificada: Politica Colombia. Esta parcialmente dentro del enfoque."

    return (
        "Consulta posiblemente fuera de alcance. El agente debe responder solo si puede "
        "conectarla con politica colombiana actual o explicar la limitacion."
    )


@tool
def obtener_contexto_temporal(input: str = "") -> str:
    """
    Retorna fecha actual y marco temporal esperado del corpus.
    """
    ahora = datetime.now()
    return (
        f"Fecha actual: {ahora.strftime('%Y-%m-%d %H:%M')}\n"
        f"Ventana objetivo del corpus: ultimos {DIAS_BUSQUEDA} dias desde la ultima descarga.\n"
        f"Enfoque configurado: {ENFOQUE_AGENTE}."
    )


@tool
def estadisticas_noticias(input: str = "") -> str:
    """
    Resume cobertura del corpus: total, fechas, categorias, temas y fuentes.
    Usala cuando el usuario pregunte que informacion tiene el agente o si hay cobertura.
    """
    try:
        noticias = _cargar_noticias()
        if not noticias:
            return "No hay noticias cargadas en datos/noticias.json."

        fechas = sorted(n.get("fecha", "") for n in noticias if n.get("fecha"))
        categorias = Counter(n.get("categoria") or "Sin categoria" for n in noticias)
        temas = Counter(n.get("tema") or "Sin tema" for n in noticias)
        fuentes = Counter(n.get("fuente") or "Sin fuente" for n in noticias)
        con_categoria = sum(1 for n in noticias if n.get("categoria"))

        lineas = [
            "Base documental del agente:",
            f"- Total de noticias: {len(noticias)}",
            f"- Rango de fechas: {fechas[0] if fechas else 'sin fecha'} a {fechas[-1] if fechas else 'sin fecha'}",
            f"- Noticias con categoria explicita: {con_categoria}/{len(noticias)}",
            "- Categorias principales:",
        ]
        for categoria, cantidad in categorias.most_common(8):
            lineas.append(f"  * {categoria}: {cantidad}")

        lineas.append("- Temas principales:")
        for tema, cantidad in temas.most_common(8):
            lineas.append(f"  * {tema}: {cantidad}")

        lineas.append("- Fuentes principales:")
        for fuente, cantidad in fuentes.most_common(8):
            lineas.append(f"  * {fuente}: {cantidad}")

        if CORPUS_METADATA.exists():
            lineas.append(f"- Metadata de corpus disponible: {CORPUS_METADATA}")
        else:
            lineas.append("- Metadata de corpus no encontrada; conviene regenerar la ingesta.")

        return "\n".join(lineas)
    except Exception as error:
        return f"No se pudo obtener estadisticas de las noticias: {error}"


@tool
def diagnosticar_cobertura(input: str = "") -> str:
    """
    Evalua si el corpus actual esta alineado con el enfoque del agente.
    Usala para decidir si una respuesta debe advertir limitaciones o pedir regenerar datos.
    """
    try:
        noticias = _cargar_noticias()
        if not noticias:
            return "Diagnostico: sin corpus cargado. Ejecuta obtener_noticias.py y crear_vectorstore.py."

        puntajes = [_score_enfoque(n) for n in noticias]
        alineadas = sum(1 for p in puntajes if p >= 3)
        porcentaje = (alineadas / len(noticias)) * 100
        fechas = sorted(n.get("fecha", "") for n in noticias if n.get("fecha"))
        con_categoria = sum(1 for n in noticias if n.get("categoria"))

        diagnostico = [
            "Diagnostico de cobertura del corpus:",
            f"- Enfoque esperado: {ENFOQUE_AGENTE}.",
            f"- Noticias alineadas por palabras clave: {alineadas}/{len(noticias)} ({porcentaje:.1f}%).",
            f"- Rango de fechas: {fechas[0] if fechas else 'sin fecha'} a {fechas[-1] if fechas else 'sin fecha'}.",
            f"- Campo categoria presente: {con_categoria}/{len(noticias)}.",
        ]

        if porcentaje < 70 or con_categoria < len(noticias) * 0.8:
            diagnostico.append(
                "Conclusion: el corpus parece mezclado o generado con una version anterior. "
                "Regenera con python3 obtener_noticias.py y python3 crear_vectorstore.py."
            )
        else:
            diagnostico.append("Conclusion: el corpus esta razonablemente alineado con el enfoque.")

        return "\n".join(diagnostico)
    except Exception as error:
        return f"No pude diagnosticar la cobertura: {error}"
