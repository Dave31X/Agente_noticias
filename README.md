# NewsAgent Intelligence Platform

NewsAgent es un agente RAG para analizar noticias de politica colombiana actual, con foco
en elecciones presidenciales Colombia 2026. La plataforma descarga noticias, filtra el
corpus por relevancia politica, crea una base vectorial local y permite consultar un
agente conversacional desde Streamlit.

## Problema y justificacion

La informacion electoral suele estar dispersa entre medios, encuestas, declaraciones,
opiniones y analisis. Para un ciudadano o estudiante no es trivial separar hechos,
interpretaciones y posibles implicaciones sin leer muchas fuentes.

Este proyecto usa un agente RAG porque:

- recupera fragmentos de noticias reales antes de responder;
- reduce alucinaciones frente a un chatbot general;
- permite explicar fuentes, fechas, cobertura y limitaciones;
- organiza consultas sobre candidatos, encuestas, partidos, instituciones y riesgos;
- mantiene un enfoque neutral para apoyar decisiones informadas, no propaganda.

El agente no busca predecir elecciones ni favorecer actores politicos. Su objetivo es
explicar contexto reciente con trazabilidad documental.

## Enfoque del agente

El foco configurado esta centralizado en [config.py](config.py):

- elecciones presidenciales Colombia 2026;
- candidatos, precandidatos, propuestas y debates;
- encuestas, favorabilidad e intencion de voto;
- partidos, coaliciones, Congreso, gobierno y oposicion;
- Registraduria, CNE, calendario y reglas electorales;
- seguridad electoral, desinformacion y riesgos democraticos.

La ventana de ingesta configurada es de los ultimos 28 dias desde cada descarga.

## Arquitectura

```text
NewsAPI / RSS fallback
  |
  v
obtener_noticias.py
  |  filtra duplicados, ruido y relevancia politico-electoral
  v
datos/noticias.json + datos/noticias.txt + datos/metadata_corpus.json
  |
  v
crear_vectorstore.py
  |  chunks + embeddings all-MiniLM-L6-v2 + metadata
  v
datos/noticias_db/  (ChromaDB)
  |
  v
tools.py
  |  retrieval, busqueda web, estadisticas, diagnostico, clasificacion, tiempo
  v
agente.py  (LangChain ReAct + Groq)
  |
  v
app.py  (Streamlit)
```

## Decisiones tecnicas clave

- **RAG local con ChromaDB:** permite consultar evidencia del corpus antes de responder.
- **Embeddings HuggingFace `all-MiniLM-L6-v2`:** modelo ligero, local y suficiente para
  busqueda semantica en fragmentos cortos.
- **Chunks de 900 caracteres con 120 de solape:** dan mas contexto que fragmentos muy
  pequenos y evitan cortar ideas importantes.
- **Metadatos por documento:** cada chunk conserva titulo, fuente, fecha, categoria,
  tema y URL para respuestas trazables.
- **Agente ReAct:** decide cuando clasificar, diagnosticar cobertura, recuperar noticias
  investigar en la web o responder limitaciones.
- **Busqueda web complementaria con Tavily:** en consultas politicas/electorales de actualidad,
  el agente combina corpus local y Tavily Search para contrastar contexto con fuentes recientes.
- **Prompt neutral:** obliga a separar hechos, interpretaciones e implicaciones, y a
  advertir si faltan datos.

## Archivos principales

- [config.py](config.py): constantes del enfoque, rutas, categorias y palabras clave.
- [obtener_noticias.py](obtener_noticias.py): ingesta desde NewsAPI con filtro estricto y fallback RSS si NewsAPI se bloquea.
- [crear_vectorstore.py](crear_vectorstore.py): crea ChromaDB desde JSON con metadatos.
- [tools.py](tools.py): herramientas que usa el agente para retrieval y diagnostico.
- [agente.py](agente.py): configura LLM, prompt ReAct y herramientas.
- [app.py](app.py): interfaz Streamlit tipo dashboard/chat.
- [evaluacion.py](evaluacion.py): casos de prueba funcionales y reporte JSON.
- [health_check.py](health_check.py): diagnostico rapido de claves, corpus y vectorstore.

## Variables de entorno

Crear `.env` local:

```env
NEWS_API_KEY=tu_clave_de_newsapi
TAVILY_API_KEY=tu_clave_de_tavily
LLM_PROVIDER=gemini
GEMINI_API_KEY=tu_clave_de_gemini
GEMINI_MODEL=gemini-1.5-flash
GEMINI_MAX_TOKENS=768
GROQ_API_KEY=tu_clave_de_groq
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_MAX_TOKENS=512
```

`.env` no deberia subirse al repositorio porque puede contener claves reales.
Si `NEWS_API_KEY` falta, vence cuota o NewsAPI responde con bloqueo, el script intenta
continuar con feeds RSS publicos configurados en [config.py](config.py). Ese fallback
sirve para no detener el proyecto, aunque puede traer menos contenido completo que
NewsAPI.
`LLM_PROVIDER=gemini` usa Gemini mediante `langchain-google-genai`.
Tambien puedes volver a Groq con `LLM_PROVIDER=groq` sin tocar codigo.
`GEMINI_MAX_TOKENS` y `GROQ_MAX_TOKENS` controlan el tamano maximo de respuesta.

## Instalacion

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Si el archivo de requisitos del entorno falla por versiones, instalar el set minimo:

```bash
pip install langchain==0.2.16 langchain-community==0.2.16 langchain-groq==0.1.9 \
  langchain-text-splitters==0.2.4 chromadb sentence-transformers streamlit \
  newspaper3k lxml_html_clean python-dotenv requests tavily-python scikit-learn pandas
```

## Flujo recomendado

```bash
python3 obtener_noticias.py
python3 crear_vectorstore.py
python3 health_check.py
streamlit run app.py
```

Para evaluar:

```bash
python3 evaluacion.py
```

La evaluacion genera `resultados/evaluacion_newsagent.json` con tiempos, criterios,
senales detectadas, fortalezas y debilidades.

## Herramientas del agente

- `buscar_noticias`: recupera hasta 7 fragmentos relevantes con fuente, fecha y URL.
- `buscar_web_noticias`: consulta Tavily Search para complementar el corpus local con web reciente.
- `clasificar_tema`: identifica si la pregunta esta dentro del enfoque.
- `obtener_contexto_temporal`: informa fecha actual y ventana esperada del corpus.
- `estadisticas_noticias`: resume total, fechas, categorias, temas y fuentes.
- `diagnosticar_cobertura`: detecta si el corpus esta mezclado, viejo o sin categorias.

## Como responde

El agente debe:

- responder en espanol claro;
- mantener neutralidad politica;
- consultar retrieval antes de responder actualidad;
- complementar con Tavily las preguntas politicas/electorales de actualidad;
- citar fuente y fecha cuando existan;
- separar hechos, interpretaciones e implicaciones;
- tratar encuestas como fotografias temporales;
- reconocer cuando el corpus no tiene evidencia suficiente;
- marcar preguntas fuera de alcance.

## Evaluacion segun rubrica

### 1. Definicion del problema

El problema es real y contextualizado: exceso de informacion electoral dispersa y dificil
de interpretar. El valor del agente esta en recuperar evidencia, resumir neutralmente y
explicar limites.

### 2. Diseno de arquitectura

La arquitectura integra ingesta, filtrado, embeddings, vector database, herramientas,
LLM, prompt especializado y UI. El flujo esta modularizado por archivos.

### 3. Implementacion tecnica

La implementacion incluye:

- filtros de relevancia que exigen Colombia + senal politica/electoral;
- deduplicacion por URL;
- extraccion de contenido completo con fallback;
- vectorstore reconstruible;
- tools con manejo de errores;
- diagnostico de cobertura para no ocultar debilidades.

### 4. Evaluacion critica

`evaluacion.py` prueba retrieval electoral, neutralidad con encuestas, separacion de
hechos/opiniones, cobertura del corpus y manejo de fuera de alcance. Tambien guarda un
reporte para analizar fallos y mejoras.

## Limitaciones

- NewsAPI puede devolver ruido si una noticia menciona Colombia de forma indirecta.
- El fallback RSS evita quedar bloqueado por cuota, pero puede devolver descripciones
  mas cortas y enlaces intermediados por el agregador.
- La calidad depende de regenerar el corpus periodicamente.
- El LLM puede responder con poca evidencia si el vectorstore esta desactualizado.
- Las encuestas no son predicciones; deben interpretarse como mediciones puntuales.
- Este sistema no reemplaza verificacion periodistica ni fuentes oficiales.

## Estado actual del corpus incluido

El corpus que venia en el repositorio parece generado con una version anterior: tiene
noticias sin `categoria` y mezcla temas economicos/internacionales. Por eso el proyecto
incluye `diagnosticar_cobertura` y se recomienda regenerar con:

```bash
python3 obtener_noticias.py
python3 crear_vectorstore.py
```

## Comandos utiles

```bash
git status --short --branch
python -m py_compile config.py obtener_noticias.py crear_vectorstore.py tools.py agente.py app.py evaluacion.py
python3 health_check.py
python3 evaluacion.py
streamlit run app.py
```
