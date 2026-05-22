import os
import time
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from config import DIAS_BUSQUEDA
from llm_provider import crear_llm
from tools import (
    buscar_noticias,
    buscar_web_noticias,
    clasificar_tema,
    obtener_contexto_temporal,
    estadisticas_noticias,
    diagnosticar_cobertura,
)

load_dotenv(override=True)

PROMPT_NEUTRAL_POLITICA = """
Eres NewsAgent, un analista neutral de politica colombiana para publico general.
Tu foco principal son las elecciones presidenciales de Colombia 2026 y el contexto politico actual.

Reglas de respuesta:
- Responde en espanol claro, sencillo y sin lenguaje tecnico innecesario.
- Mantente neutral: no favorezcas candidatos, partidos, gobierno u oposicion.
- Separa hechos, interpretaciones y posibles implicaciones cuando sea util.
- Para preguntas de actualidad o datos concretos, consulta buscar_noticias antes de responder.
{reglas_web}
- Si el usuario pregunta que informacion tienes, usa estadisticas_noticias y diagnosticar_cobertura.
- Si una afirmacion viene de una noticia o medio, presentala como reporte o version de esa fuente.
- Incluye fuente y fecha cuando el retrieval las entregue.
- No conviertas opiniones de medios, politicos o encuestas en hechos definitivos.
- Cuando hables de encuestas, menciona que son fotografias de un momento y pueden cambiar.
- Responde siempre con la mejor informacion disponible. Si el corpus local es debil, usa Tavily y responde con esa evidencia.
- No empieces diciendo que no tienes informacion suficiente si hay al menos una fuente recuperada.
- Si hay incertidumbre, respondela como incertidumbre concreta al final, no como negativa inicial.
- Si una pregunta esta parcialmente fuera del enfoque, responde la parte general brevemente y conectala con politica colombiana si aplica.
- Para preguntas amplias, organiza la respuesta en resumen, puntos clave y que significa para la gente.
- Prioriza informacion reciente de los ultimos {dias_busqueda} dias cuando este disponible.
- Menciona limitaciones solo al final y solo si cambian la interpretacion de la respuesta.

Puedes usar estas herramientas:

{tools}

Usa este formato:

Question: la pregunta del usuario
Thought: piensa brevemente que necesitas consultar
Action: una de [{tool_names}]
Action Input: el texto de busqueda o entrada para la herramienta
Observation: resultado de la herramienta
... puedes repetir Thought/Action/Action Input/Observation si hace falta
Thought: ya tengo suficiente informacion para responder
Final Answer: respuesta final en espanol neutral y facil de entender

Question: {input}
Thought:{agent_scratchpad}
"""


def crear_agente(max_tokens: int | None = None, permitir_web: bool = True):
    # Permite controlar `max_tokens` por variable de entorno `GROQ_MAX_TOKENS`
    if max_tokens is None:
        try:
            max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "384"))
        except Exception:
            max_tokens = 384

    llm = crear_llm(temperature=0.3, max_tokens=max_tokens)

    tools = [
        buscar_noticias,
        clasificar_tema,
        obtener_contexto_temporal,
        estadisticas_noticias,
        diagnosticar_cobertura,
    ]
    if permitir_web:
        tools.append(buscar_web_noticias)

    reglas_web = ""
    if permitir_web:
        reglas_web = (
            "- Para preguntas dentro del enfoque politico/electoral, usa buscar_noticias y despues buscar_web_noticias: "
            "el corpus local da contexto y Tavily da contraste/actualidad.\n"
            "- No dejes la web solo como respaldo: usala como complemento habitual cuando la consulta trate de actualidad, "
            "elecciones, candidatos, encuestas, instituciones, partidos, gobierno, oposicion o riesgos.\n"
            "- Distingue claramente que viene del corpus local y que viene de Tavily.\n"
            "- Si el corpus local y Tavily difieren, explica la diferencia sin bloquear la respuesta.\n"
            "- Si usas web, cita titulo, medio/fuente, fecha y URL cuando esten disponibles."
        )

    prompt = PromptTemplate.from_template(
        PROMPT_NEUTRAL_POLITICA
        .replace("{dias_busqueda}", str(DIAS_BUSQUEDA))
        .replace("{reglas_web}", reglas_web)
    )

    agente = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    ejecutor = AgentExecutor(
        agent=agente,
        tools=tools,
        verbose=False,
        max_iterations=5,
        max_execution_time=45,
        handle_parsing_errors=True,
    )

    return ejecutor


def invoke_with_retries(ejecutor, input_obj, retries: int = 3, initial_delay: int = 5, backoff: int = 2):
    """Invoca el ejecutor y reintenta en caso de rate limit (429 / tokens).

    Detecta cadenas comunes de error de cuota y reintenta exponencialmente.
    """
    delay = initial_delay
    for attempt in range(1, retries + 1):
        try:
            return ejecutor.invoke(input_obj)
        except Exception as e:
            text = str(e) or ""
            is_rate = "429" in text or "rate limit" in text.lower() or "rate_limit_exceeded" in text
            if not is_rate:
                raise
            if attempt == retries:
                raise
            print(f"WARN: rate limit detectado, reintentando en {delay}s (intento {attempt}/{retries})")
            time.sleep(delay)
            delay *= backoff


# Prueba directa
if __name__ == "__main__":
    print("🤖 Iniciando agente...\n")
    agente = crear_agente()

    pregunta = "¿Qué está pasando con las elecciones presidenciales en Colombia?"
    print(f"👤 Pregunta: {pregunta}\n")
    print("─" * 50)

    try:
        respuesta = invoke_with_retries(agente, {"input": pregunta}, retries=4, initial_delay=10)
        print("\n📝 Respuesta final:")
        print(respuesta["output"])
    except Exception as e:
        print("\n❌ Error al invocar agente:")
        print(e)
