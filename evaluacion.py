# evaluacion.py
# Evaluacion funcional y critica del agente contra la rubrica del proyecto.

import json
import time
from datetime import datetime
from pathlib import Path

from agente import crear_agente
from tools import diagnosticar_cobertura, estadisticas_noticias

RESULTADOS_DIR = Path("resultados")
RESULTADOS_DIR.mkdir(exist_ok=True)


CASOS_PRUEBA = [
    {
        "id": "retrieval_electoral",
        "pregunta": "¿Qué está pasando con las elecciones presidenciales en Colombia?",
        "espera": ["fuente", "fecha", "elecciones", "colombia"],
        "descripcion": "Debe recuperar noticias y sintetizar contexto electoral.",
    },
    {
        "id": "neutralidad_encuestas",
        "pregunta": "¿Qué dicen las encuestas y qué límites tienen?",
        "espera": ["encuesta", "momento", "pueden cambiar"],
        "descripcion": "Debe tratar encuestas como fotografia temporal, no prediccion.",
    },
    {
        "id": "hechos_interpretaciones",
        "pregunta": "Sepárame hechos, interpretaciones e implicaciones del debate político actual.",
        "espera": ["hechos", "interpretaciones", "implicaciones"],
        "descripcion": "Debe estructurar la respuesta y no mezclar opinion con hecho.",
    },
    {
        "id": "cobertura",
        "pregunta": "¿Qué información tienes disponible y qué limitaciones tiene la base?",
        "espera": ["total", "fechas", "limitaciones"],
        "descripcion": "Debe reconocer cobertura, fechas y debilidades del corpus.",
    },
    {
        "id": "web_complementaria",
        "pregunta": "Contrasta el corpus local con web reciente sobre elecciones presidenciales en Colombia y aclara las fuentes.",
        "espera": ["corpus", "web", "fuente", "fecha"],
        "descripcion": "Debe usar RAG local y busqueda web como fuentes complementarias.",
    },
    {
        "id": "fuera_de_alcance",
        "pregunta": "¿Cuál es el mejor celular para comprar este mes?",
        "espera": ["fuera", "enfoque", "politica"],
        "descripcion": "Debe marcar la consulta como fuera del foco del agente.",
    },
]


def contiene_senales(texto, senales):
    texto_lower = texto.lower()
    return [senal for senal in senales if senal.lower() in texto_lower]


def evaluar_agente():
    print("=" * 72)
    print("EVALUACION NEWSAGENT - RAG POLITICA COLOMBIA")
    print("=" * 72)
    print("\nDiagnostico inicial del corpus:\n")
    print(diagnosticar_cobertura.invoke(""))
    print("\nEstadisticas:\n")
    print(estadisticas_noticias.invoke(""))

    agente = crear_agente()
    resultados = []

    for caso in CASOS_PRUEBA:
        print("\n" + "-" * 72)
        print(f"CASO: {caso['id']}")
        print(f"Pregunta: {caso['pregunta']}")
        print(f"Criterio: {caso['descripcion']}")

        inicio = time.time()
        try:
            respuesta = agente.invoke({"input": caso["pregunta"]}).get("output", "")
            error = None
        except Exception as exc:
            respuesta = ""
            error = str(exc)
        tiempo = round(time.time() - inicio, 2)

        senales = contiene_senales(respuesta, caso["espera"])
        cobertura_senales = len(senales) / len(caso["espera"])
        aprobado = error is None and cobertura_senales >= 0.5 and len(respuesta) > 120

        resultado = {
            "id": caso["id"],
            "pregunta": caso["pregunta"],
            "descripcion": caso["descripcion"],
            "tiempo_segundos": tiempo,
            "aprobado": aprobado,
            "senales_esperadas": caso["espera"],
            "senales_detectadas": senales,
            "respuesta": respuesta,
            "error": error,
        }
        resultados.append(resultado)

        estado = "APROBADO" if aprobado else "REVISAR"
        print(f"Estado: {estado} | Tiempo: {tiempo}s | Senales: {senales}")
        if error:
            print(f"Error: {error}")
        else:
            print(f"Respuesta corta: {respuesta[:360]}...")

    aprobados = sum(1 for r in resultados if r["aprobado"])
    reporte = {
        "generado_en": datetime.now().isoformat(timespec="seconds"),
        "total_casos": len(resultados),
        "aprobados": aprobados,
        "porcentaje_aprobacion": round((aprobados / len(resultados)) * 100, 2),
        "fortalezas": [
            "Arquitectura RAG modular con ingesta, vectorstore, herramientas y UI separadas.",
            "Prompt especializado en neutralidad politica y uso explicito de retrieval.",
            "Evaluacion incluye cobertura, neutralidad, estructura y fuera de alcance.",
        ],
        "debilidades_a_vigilar": [
            "La calidad factual depende de que el corpus se regenere periodicamente.",
            "NewsAPI puede traer ruido si una busqueda coincide por menciones indirectas.",
            "El LLM puede omitir fuentes si el prompt no encuentra documentos suficientes.",
        ],
        "resultados": resultados,
    }

    salida = RESULTADOS_DIR / "evaluacion_newsagent.json"
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 72)
    print("RESUMEN")
    print("=" * 72)
    print(f"Casos aprobados: {aprobados}/{len(resultados)}")
    print(f"Reporte guardado en: {salida}")
    return reporte


if __name__ == "__main__":
    evaluar_agente()
