"""Shared chat orchestration for Streamlit and the React API."""

from langchain_core.messages import HumanMessage, SystemMessage

from llm_provider import crear_llm


WEB_ERROR_PREFIXES = (
    "La busqueda web con Tavily no esta configurada",
    "No pude investigar en la web con Tavily",
    "Tavily no encontro resultados web recientes",
)


def detectar_intencion(pregunta: str) -> str:
    texto = pregunta.lower()
    if any(palabra in texto for palabra in ["vicepresidente", "vicepresidenta", "vicepresidencial", "formula", "fórmula"]):
        return "formulas_vicepresidenciales"
    if any(palabra in texto for palabra in ["encuesta", "favorabilidad", "intencion de voto", "intención de voto", "top"]):
        return "encuestas_top"
    if any(palabra in texto for palabra in ["propuesta", "propuestas", "programa", "apolitico", "apolítico", "no estoy muy enterado"]):
        return "propuestas_pedagogicas"
    if any(palabra in texto for palabra in ["quien es", "quién es", "perfil", "trayectoria", "hoja de vida"]):
        return "perfil_candidato"
    return "general"


def construir_consulta_retrieval(pregunta: str) -> str:
    pregunta_normalizada = (
        pregunta.replace("Ceoeda", "Cepeda")
        .replace("ceoeda", "cepeda")
        .replace("preseidencia", "presidencia")
    )
    pregunta_lower = pregunta_normalizada.lower()
    intencion = detectar_intencion(pregunta_normalizada)

    if intencion == "formulas_vicepresidenciales":
        return (
            f"{pregunta_normalizada}\n"
            "formulas vicepresidenciales fórmula vicepresidencial vicepresidente vicepresidenta "
            "candidatos presidenciales Colombia 2026 lista completa Registraduria inscritos nombres"
        )

    if intencion == "encuestas_top":
        return (
            f"{pregunta_normalizada}\n"
            "encuestas presidenciales Colombia 2026 intención de voto favorabilidad candidatos top "
            "medición sondeo ranking primera vuelta"
        )

    senales_ivan_cepeda = [
        "ivan cepeda",
        "iván cepeda",
        "cepeda",
    ]
    if any(senal in pregunta_lower for senal in senales_ivan_cepeda):
        return (
            f"{pregunta_normalizada}\n"
            "Ivan Cepeda Colombia senador derechos humanos Pacto Historico candidato presidencial 2026 "
            "encuestas propuestas trayectoria perfil politico fuentes"
        )

    if intencion == "propuestas_pedagogicas":
        return (
            f"{pregunta_normalizada}\n"
            "propuestas candidatos presidenciales Colombia 2026 programa de gobierno "
            "educacion salud economia empleo seguridad paz inteligencia artificial autonomia debates jovenes"
        )
    return pregunta_normalizada


def buscar_coincidencias_lexicas(pregunta: str, limite: int = 5) -> str:
    import json
    import re

    from config import NEWS_JSON

    if not NEWS_JSON.exists():
        return ""

    intencion = detectar_intencion(pregunta)
    texto = pregunta.lower()
    palabras = set(re.findall(r"[a-záéíóúñü]{4,}", texto))
    extras_por_intencion = {
        "formulas_vicepresidenciales": {
            "formula",
            "fórmula",
            "formulas",
            "fórmulas",
            "vicepresidencial",
            "vicepresidente",
            "vicepresidenta",
            "inscritos",
            "registraduria",
        },
        "propuestas_pedagogicas": {
            "propuestas",
            "programa",
            "educacion",
            "salud",
            "economia",
            "empleo",
            "seguridad",
            "inteligencia",
            "autonomia",
        },
        "encuestas_top": {
            "encuesta",
            "encuestas",
            "favorabilidad",
            "intencion",
            "voto",
            "top",
            "ranking",
        },
    }
    palabras.update(extras_por_intencion.get(intencion, set()))

    try:
        with open(NEWS_JSON, "r", encoding="utf-8") as archivo:
            noticias = json.load(archivo)
    except Exception:
        return ""

    resultados = []
    for noticia in noticias if isinstance(noticias, list) else []:
        titulo = noticia.get("titulo", "")
        descripcion = noticia.get("descripcion", "")
        contenido = noticia.get("contenido", "")
        combinado = " ".join([titulo, descripcion, contenido]).lower()
        puntaje = sum(3 for palabra in palabras if palabra in titulo.lower())
        puntaje += sum(1 for palabra in palabras if palabra in combinado)
        if intencion == "formulas_vicepresidenciales" and "vicepresidencial" in combinado:
            puntaje += 8
        if intencion == "propuestas_pedagogicas" and "propuesta" in combinado:
            puntaje += 5
        if puntaje > 0:
            resultados.append((puntaje, noticia))

    if not resultados:
        return ""

    lineas = ["Coincidencias exactas en el corpus JSON:"]
    for indice, (_, noticia) in enumerate(sorted(resultados, key=lambda item: item[0], reverse=True)[:limite], 1):
        fragmento = " ".join((noticia.get("contenido") or noticia.get("descripcion") or "").split())[:700]
        lineas.extend(
            [
                f"\n--- Coincidencia {indice} ---",
                f"Titulo: {noticia.get('titulo', 'Sin titulo')}",
                f"Fuente: {noticia.get('fuente', 'Sin fuente')}",
                f"Fecha: {noticia.get('fecha', 'Sin fecha')}",
                f"Categoria: {noticia.get('categoria', 'Sin categoria')}",
                f"Fragmento JSON: {fragmento or 'Sin contenido adicional en el corpus.'}",
            ]
        )
    return "\n".join(lineas)


def preparar_prompt_chat(pregunta: str, permitir_web: bool = True):
    from tools import buscar_noticias, buscar_web_noticias

    consulta_retrieval = construir_consulta_retrieval(pregunta)
    intencion = detectar_intencion(pregunta)
    contexto_lexico = buscar_coincidencias_lexicas(pregunta)
    contexto_local = buscar_noticias.invoke(consulta_retrieval)
    contexto_web = ""
    if permitir_web:
        contexto_web = buscar_web_noticias.invoke(consulta_retrieval)
        if any(contexto_web.startswith(prefix) for prefix in WEB_ERROR_PREFIXES):
            contexto_web = ""

    sistema = (
        "Eres NewsAgent, analista neutral de politica colombiana. "
        "Responde siempre con la mejor informacion disponible como un compendio integrado. "
        "Usa el corpus local como contexto y Tavily como complemento web cuando exista. "
        "Si el usuario pide orientacion basica, explica con lenguaje sencillo y sin asumir conocimiento previo. "
        "No respondas con motivacion generica: aterriza en candidatos, temas y propuestas recuperadas. "
        "Si el usuario escribe un nombre con typo evidente, corrige el nombre y dilo de forma breve. "
        "No empieces diciendo que no tienes informacion suficiente si hay fuentes. "
        "Si hay incertidumbre, ponla al final como limitacion concreta. "
        "Separa hechos de interpretaciones cuando ayude, pero evita responder noticia por noticia. "
        "Adapta la respuesta a la pregunta concreta; no reutilices siempre el mismo esquema de seguridad, economia, salud y educacion. "
        "Si preguntan por nombres, listas, fechas o formulas, intenta responder en formato directo y solo usa contexto general si esos datos no aparecen. "
        "No incluyas una seccion de fuentes, links, URLs ni markdown de enlaces a menos que el usuario lo pida explicitamente. "
        "Puedes mencionar de forma natural que el contexto viene de prensa reciente o busqueda web, sin listar medios. "
        "Si la busqueda web no trae resultados o falla tecnicamente, no lo menciones al usuario; responde con el corpus local disponible. "
        "Cierra con una conclusion breve o una limitacion concreta; no termines en una frase incompleta."
    )
    usuario = f"""
Pregunta del usuario:
{pregunta}

Intencion detectada:
{intencion}

Consulta usada para recuperar contexto:
{consulta_retrieval}

Coincidencias textuales adicionales:
{contexto_lexico or 'No hubo coincidencias textuales adicionales.'}

Contexto recuperado del corpus local:
{contexto_local}

Contexto recuperado de Tavily/web:
{contexto_web or 'Sin contexto web adicional util para esta consulta.'}

Redacta una respuesta util en espanol como un compendio, no como ideas sueltas por cada noticia.
Agrupa patrones, consensos, tensiones y diferencias entre las noticias recuperadas.
Reglas por intencion:
- formulas_vicepresidenciales: responde primero si el corpus trae nombres concretos. Si solo trae titulos de notas sin nombres, dilo de forma directa y explica que el corpus confirma que hay notas sobre formulas, pero no conserva la lista completa. No cambies el tema hacia propuestas generales.
- propuestas_pedagogicas: explica por candidato o por bloques politicos solo cuando el contexto lo permita; si no hay detalle por candidato, dilo y organiza una guia honesta sobre que mirar en debates/programas sin fingir propuestas especificas.
- encuestas_top: separa mediciones, candidatos mencionados y advertencias; no trates encuestas como prediccion.
- general: responde con la estructura que mejor encaje con la pregunta.

Evita saludos largos y frases de relleno. La respuesta debe ser completa, neutral y basada en las noticias recuperadas.
"""
    return [SystemMessage(content=sistema), HumanMessage(content=usuario)]


def responder_directo(pregunta: str, permitir_web: bool = True) -> str:
    llm = crear_llm(temperature=0.25, max_tokens=2200)
    mensajes = preparar_prompt_chat(pregunta, permitir_web=permitir_web)
    respuesta = llm.invoke(mensajes).content
    if respuesta and respuesta.rstrip()[-1] not in ".!?)…":
        mensajes.append(
            HumanMessage(
                content=(
                    "La respuesta anterior quedo incompleta. Reescribela completa, "
                    "mas concisa, como compendio y sin lista de fuentes."
                )
            )
        )
        respuesta = llm.invoke(mensajes).content
    return respuesta


def stream_respuesta(pregunta: str, permitir_web: bool = True):
    llm = crear_llm(temperature=0.25, max_tokens=2200)
    mensajes = preparar_prompt_chat(pregunta, permitir_web=permitir_web)
    for chunk in llm.stream(mensajes):
        contenido = getattr(chunk, "content", "")
        if isinstance(contenido, list):
            contenido = "".join(str(parte) for parte in contenido)
        if contenido:
            yield str(contenido)
