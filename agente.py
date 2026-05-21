# 4_agente.py

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from tools import (
    buscar_noticias,
    clasificar_tema,
    obtener_contexto_temporal,
    estadisticas_noticias
)

load_dotenv()

PROMPT_NEUTRAL_POLITICA = """
Eres NewsAgent, un analista neutral de politica colombiana para publico general.
Tu foco principal son las elecciones presidenciales de Colombia 2026 y el contexto politico actual.

Reglas de respuesta:
- Responde en espanol claro, sencillo y sin lenguaje tecnico innecesario.
- Mantente neutral: no favorezcas candidatos, partidos, gobierno u oposicion.
- Separa hechos, interpretaciones y posibles implicaciones cuando sea util.
- Si una afirmacion viene de una noticia o medio, presentala como reporte o version de esa fuente.
- No conviertas opiniones de medios, politicos o encuestas en hechos definitivos.
- Cuando hables de encuestas, menciona que son fotografias de un momento y pueden cambiar.
- Si faltan datos en la base, dilo con claridad y evita inventar informacion.
- Para preguntas amplias, organiza la respuesta en resumen, puntos clave y que significa para la gente.
- Prioriza informacion reciente de los ultimos 30 dias cuando este disponible.

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

def crear_agente():
    # 1. LLM con Groq (gratis)
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=1024
    )

    # 2. Herramientas disponibles
    tools = [
        buscar_noticias,
        clasificar_tema,
        obtener_contexto_temporal,
        estadisticas_noticias
    ]

    # 3. Prompt ReAct especializado en politica colombiana neutral
    prompt = PromptTemplate.from_template(PROMPT_NEUTRAL_POLITICA)

    # 4. Crear agente ReAct
    agente = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    # 5. Ejecutor del agente
    ejecutor = AgentExecutor(
         agent=agente,
        tools=tools,
        verbose=True,
        max_iterations=10,      # ← sube de 6 a 10
        max_execution_time=60,  # ← agrega este límite de 60 segundos
        handle_parsing_errors=True
    )

    return ejecutor


# Prueba directa
if __name__ == "__main__":
    print("🤖 Iniciando agente...\n")
    agente = crear_agente()

    pregunta = "¿Qué está pasando con las elecciones presidenciales en Colombia?"
    print(f"👤 Pregunta: {pregunta}\n")
    print("─" * 50)

    respuesta = agente.invoke({"input": pregunta})
    print("\n📝 Respuesta final:")
    print(respuesta["output"])
