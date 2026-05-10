# 4_agente.py

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from tools import (
    buscar_noticias,
    clasificar_tema,
    obtener_contexto_temporal,
    estadisticas_noticias
)

load_dotenv()

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

    # 3. Prompt ReAct desde LangChain Hub
    prompt = hub.pull("hwchase17/react")

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

    pregunta = "¿Qué está pasando con la economía en Colombia?"
    print(f"👤 Pregunta: {pregunta}\n")
    print("─" * 50)

    respuesta = agente.invoke({"input": pregunta})
    print("\n📝 Respuesta final:")
    print(respuesta["output"])