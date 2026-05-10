# 6_evaluacion.py
# Evalúa el desempeño del agente con preguntas de prueba

import time
from agente import crear_agente

def evaluar_agente():
    agente = crear_agente()
    
    preguntas = [
        "¿Qué está pasando con la economía colombiana?",
        "¿Hay noticias relevantes sobre inteligencia artificial?",
        "¿Qué información tienes disponible?",
        "¿Qué debería saber un inversionista hoy?",
        "Resume las noticias políticas más importantes"
    ]
    
    print("=" * 60)
    print("EVALUACIÓN DEL AGENTE DE NOTICIAS")
    print("=" * 60)
    
    resultados = []
    for i, pregunta in enumerate(preguntas, 1):
        print(f"\n📌 Pregunta {i}: {pregunta}")
        print("-" * 40)
        
        inicio = time.time()
        respuesta = agente.invoke({"input": pregunta})
        tiempo = round(time.time() - inicio, 2)
        
        resultado = {
            "pregunta": pregunta,
            "respuesta": respuesta["output"],
            "tiempo_segundos": tiempo
        }
        resultados.append(resultado)
        
        print(f"✅ Respuesta: {respuesta['output'][:200]}...")
        print(f"⏱️  Tiempo: {tiempo}s")
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN DE EVALUACIÓN")
    print("=" * 60)
    print(f"Total preguntas: {len(preguntas)}")
    print(f"Tiempo promedio: {sum(r['tiempo_segundos'] for r in resultados)/len(resultados):.2f}s")
    print("Todas las preguntas respondidas: ✅")

if __name__ == "__main__":
    evaluar_agente()