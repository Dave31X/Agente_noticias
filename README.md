# NewsAgent Intelligence Platform

NewsAgent Intelligence Platform es una aplicacion de analisis de noticias basada en RAG
(`Retrieval-Augmented Generation`). El proyecto descarga noticias, las convierte en una
base vectorial y permite consultarlas desde una interfaz web en Streamlit usando un
agente conversacional con LangChain y Groq.

El enfoque configurado ahora esta centrado en politica actual de Colombia, especialmente
elecciones presidenciales 2026, con contexto politico nacional, candidatos, encuestas,
partidos, coaliciones, instituciones electorales y riesgos electorales.

La ventana de busqueda configurada es de los ultimos 30 dias.

## Que hace el proyecto

- Descarga noticias desde NewsAPI usando consultas tematicas predefinidas.
- Filtra articulos relevantes para politica colombiana, elecciones presidenciales y
  contexto electoral.
- Intenta extraer el contenido completo de cada noticia con `newspaper3k`.
- Guarda el corpus en formatos JSON y TXT.
- Divide las noticias en fragmentos pequenos para busqueda semantica.
- Crea una base vectorial local con ChromaDB.
- Expone herramientas de busqueda y analisis para un agente LangChain.
- Ofrece una interfaz web profesional con Streamlit para hacer preguntas al agente.

## Arquitectura general

```text
NewsAPI
  |
  v
obtener_noticias.py
  |
  +-- datos/noticias.json
  +-- datos/noticias.txt
          |
          v
crear_vectorstore.py
          |
          v
datos/noticias_db/  (ChromaDB)
          |
          v
tools.py
          |
          v
agente.py  (LangChain + Groq)
          |
          v
app.py  (Streamlit)
```

## Estructura del repositorio

```text
.
├── README.md
├── requirements.txt
├── .env
├── .gitignore
├── app.py
├── agente.py
├── tools.py
├── obtener_noticias.py
├── crear_vectorstore.py
├── evaluacion.py
├── datos/
│   ├── noticias.json
│   ├── noticias.txt
│   └── noticias_db/
│       ├── chroma.sqlite3
│       └── ...
└── __pycache__/
```

## Archivos principales

### `app.py`

Es la interfaz principal del proyecto. Usa Streamlit para construir una experiencia web
tipo dashboard/chat.

Responsabilidades principales:

- Configura la pagina de Streamlit.
- Carga `datos/noticias.json`.
- Calcula estadisticas del corpus:
  - total de noticias
  - numero de fuentes
  - numero de temas
  - fecha mas reciente
  - fuentes principales
  - temas principales
- Inicializa el agente usando `crear_agente()`.
- Renderiza:
  - sidebar con estado del sistema
  - metricas principales
  - preguntas sugeridas
  - chat conversacional
- Procesa preguntas del usuario y envia la consulta al agente.

Comando recomendado para ejecutarlo:

```bash
streamlit run app.py
```

La interfaz muestra los comandos reales del proyecto: `obtener_noticias.py`,
`crear_vectorstore.py` y `app.py`.

### `agente.py`

Crea el agente conversacional.

Componentes principales:

- Carga variables de entorno con `python-dotenv`.
- Usa `ChatGroq` como LLM.
- Modelo configurado:

```python
llama-3.3-70b-versatile
```

- Temperatura configurada: `0.3`.
- Max tokens configurado: `1024`.
- Usa un agente tipo ReAct de LangChain.
- Usa un prompt ReAct local especializado en politica colombiana neutral.
- Registra las herramientas definidas en `tools.py`.
- Crea un `AgentExecutor` con:
  - `max_iterations=10`
  - `max_execution_time=60`
  - `handle_parsing_errors=True`

Tambien incluye una prueba directa si se ejecuta como script:

```bash
python3 agente.py
```

### `tools.py`

Define las herramientas que puede usar el agente.

Carga la base vectorial local:

```python
vectorstore = Chroma(
    persist_directory="./datos/noticias_db",
    embedding_function=embeddings
)
```

Modelo de embeddings usado:

```python
all-MiniLM-L6-v2
```

Herramientas disponibles:

#### `buscar_noticias(consulta: str)`

Busca noticias relevantes en ChromaDB usando similitud semantica.

- Recibe una consulta de texto.
- Ejecuta `similarity_search`.
- Devuelve hasta 6 resultados relevantes.
- Incluye fragmentos del contenido encontrado.

#### `clasificar_tema(consulta: str)`

Clasifica una consulta segun palabras clave.

Categorias soportadas:

- Elecciones presidenciales
- Politica Colombia
- Economia
- Tecnologia
- Deportes
- Salud
- General / Actualidad

#### `obtener_contexto_temporal(input: str = "")`

Devuelve fecha y hora actuales, mas una nota indicando que el enfoque configurado busca
noticias de los ultimos 30 dias.

#### `estadisticas_noticias(input: str = "")`

Lee `datos/noticias.json` y devuelve un resumen basico de la base.

Nota: esta herramienta intenta agrupar por el campo `tema`. El corpus actual si trae
`tema`, pero no trae `categoria`.

### `obtener_noticias.py`

Script de ingesta de noticias desde NewsAPI. Esta configurado para buscar politica
actual de Colombia, especialmente elecciones presidenciales 2026.

Responsabilidades:

- Cargar `NEWS_API_KEY` desde `.env`.
- Definir una lista amplia de temas de busqueda electoral y politica.
- Consultar NewsAPI por cada tema.
- Controlar parcialmente limites de rate limit.
- Filtrar noticias duplicadas por URL.
- Filtrar noticias poco relevantes.
- Intentar descargar contenido completo con `newspaper3k`.
- Guardar resultados en:
  - `datos/noticias.json`
  - `datos/noticias.txt`

El script organiza temas en estas categorias:

- Elecciones presidenciales Colombia 2026
- Candidatos y propuestas
- Encuestas y opinion publica
- Partidos, coaliciones y Congreso
- Instituciones y reglas electorales
- Gobierno y contexto politico
- Seguridad y riesgos electorales

Ejecutar descarga:

```bash
python3 obtener_noticias.py
```

Variables importantes:

```python
PAGINAS_POR_TEMA = 2
MAX_SOLICITUDES_POR_HORA = 90
DIAS_BUSQUEDA = 30
```

El script consulta hasta 2 paginas por tema, con hasta 100 articulos por pagina.

### `crear_vectorstore.py`

Script encargado de construir la base vectorial.

Responsabilidades:

- Leer `datos/noticias.txt`.
- Separar noticias usando el delimitador `=== NOTICIA`.
- Convertir cada noticia en un `Document` de LangChain.
- Dividir documentos en chunks.
- Generar embeddings con HuggingFace.
- Persistir la base en `datos/noticias_db/`.

Configuracion de chunks:

```python
chunk_size = 500
chunk_overlap = 50
```

Ejecutar generacion de vectorstore:

```bash
python3 crear_vectorstore.py
```

### `evaluacion.py`

Script de evaluacion manual.

Hace preguntas de prueba al agente y mide tiempos de respuesta.

Preguntas incluidas originalmente:

- Que esta pasando con la economia colombiana?
- Hay noticias relevantes sobre inteligencia artificial?
- Que informacion tienes disponible?
- Que deberia saber un inversionista hoy?
- Resume las noticias politicas mas importantes.

Ejecutar:

```bash
python3 evaluacion.py
```

## Datos incluidos

El repositorio ya trae datos versionados en `datos/`.

Estado observado del corpus:

- Total aproximado: `1217` noticias.
- Archivo JSON: `datos/noticias.json`.
- Archivo TXT para RAG: `datos/noticias.txt`.
- Base vectorial: `datos/noticias_db/`.
- Rango de fechas observado: `2026-03-30` a `2026-04-28`.

Campos presentes en `datos/noticias.json`:

```text
contenido
contenido_parcial
descripcion
fecha
fuente
tema
titulo
url
```

Fuentes principales observadas:

- La Nacion
- Latercera.com
- Jornada.com.mx
- Www.abc.es
- Diario EL PAIS Uruguay
- El Financiero
- Nacion.com
- Elperiodico.com
- RT
- Www.df.cl

Nota importante: el codigo actual de `obtener_noticias.py` guarda un campo `categoria`,
pero el JSON incluido actualmente no lo trae. Esto sugiere que el corpus versionado fue
generado con una version anterior o distinta del pipeline.

## Variables de entorno

El archivo `.env` debe tener:

```env
NEWS_API_KEY=tu_clave_de_newsapi
GROQ_API_KEY=tu_clave_de_groq
```

Uso de cada clave:

- `NEWS_API_KEY`: necesaria para descargar noticias con `obtener_noticias.py`.
- `GROQ_API_KEY`: necesaria para usar el LLM desde `agente.py` y `app.py`.

## Instalacion

Crear entorno virtual:

```bash
python3 -m venv venv
```

Activarlo:

```bash
source venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Ejecucion rapida

Si ya existen `datos/noticias.json`, `datos/noticias.txt` y `datos/noticias_db/`, se puede
ejecutar directamente la app:

```bash
streamlit run app.py
```

Luego abrir la URL local que muestre Streamlit, normalmente:

```text
http://localhost:8501
```

## Regenerar noticias y base vectorial

Flujo completo recomendado:

```bash
python3 obtener_noticias.py
python3 crear_vectorstore.py
streamlit run app.py
```

Este proceso:

1. Descarga noticias nuevas de los ultimos 30 dias.
2. Guarda JSON y TXT.
3. Reconstruye ChromaDB.
4. Abre la interfaz para consultar el agente.

Con la configuracion actual, la descarga se centra en:

- elecciones presidenciales Colombia 2026
- candidatos, precandidatos y campanas
- encuestas e intencion de voto
- partidos, coaliciones y Congreso
- Registraduria, CNE, reglas y calendario electoral
- Gobierno Petro, oposicion y contexto politico
- seguridad electoral, desinformacion y riesgos

## Dependencias principales

El proyecto usa muchas dependencias, pero las mas importantes son:

- `streamlit`: interfaz web.
- `langchain`: agentes, herramientas y flujo RAG.
- `langchain-groq`: integracion con Groq.
- `groq`: cliente de Groq.
- `chromadb`: base vectorial local.
- `sentence-transformers`: embeddings locales.
- `langchain-community`: integraciones comunitarias de LangChain.
- `newspaper3k`: extraccion de contenido de articulos.
- `requests`: consumo de NewsAPI.
- `python-dotenv`: carga de variables de entorno.
- `pandas`, `scikit-learn`, `numpy`: dependencias de analisis y soporte.

## Flujo de pregunta en la app

Cuando el usuario escribe una pregunta en la interfaz:

1. `app.py` recibe el texto desde `st.chat_input`.
2. Se llama a `procesar_pregunta()`.
3. La pregunta se agrega al historial de Streamlit.
4. El agente se invoca con:

```python
st.session_state.agente.invoke({"input": pregunta})
```

5. El agente decide que herramientas usar.
6. Si necesita contexto documental, usa `buscar_noticias`.
7. `buscar_noticias` consulta ChromaDB.
8. El LLM genera una respuesta final.
9. La respuesta se muestra en el chat.

## Estado de versionamiento observado

`.gitignore` contiene:

```text
venv/
datos/
.env
__pycache__/
*.pyc
```

Sin embargo, en el repositorio clonado ya aparecen versionados:

- `.env`
- `datos/`
- `__pycache__/`

Esto significa que aunque ahora esten ignorados, Git ya los estaba siguiendo. Si se desea
limpiar el repositorio, habria que retirarlos del indice con cuidado y sin borrar los
archivos locales.

## Pruebas

No se encontraron pruebas automatizadas ni configuracion de `pytest`.

La validacion disponible es manual mediante:

```bash
python3 evaluacion.py
```

Tambien se puede probar la app directamente con preguntas desde Streamlit.

## Neutralidad esperada del agente

El agente fue configurado para responder con tono neutral y sencillo. Sus respuestas deben:

- No favorecer candidatos, partidos, gobierno u oposicion.
- Separar hechos, interpretaciones y posibles implicaciones.
- Presentar opiniones de medios o actores politicos como opiniones, no como hechos.
- Tratar las encuestas como fotografias de un momento, no como predicciones definitivas.
- Decir claramente cuando no tenga datos suficientes en la base.
- Explicar para publico general, evitando lenguaje tecnico innecesario.

## Riesgos y puntos a revisar

- El README original estaba vacio, por lo que esta documentacion reconstruye el
  comportamiento desde el codigo actual.
- El archivo `.env` esta versionado, aunque aparece en `.gitignore`. Esto puede ser un
  riesgo si contiene claves reales.
- `datos/` esta versionado aunque tambien aparece en `.gitignore`.
- `__pycache__/` esta versionado aunque deberia ser generado localmente.
- `tools.py` carga el vectorstore al importar el modulo. Si falta `datos/noticias_db/`,
  la inicializacion del agente puede fallar.
- El campo `categoria` se guarda en el pipeline nuevo, pero no existe en el JSON incluido.
- El corpus incluido originalmente puede no reflejar todavia el nuevo enfoque hasta que se
  ejecuten `obtener_noticias.py` y `crear_vectorstore.py`.
- No hay manejo detallado de errores para respuestas inesperadas de NewsAPI.
- No hay suite de tests automatizados.

## Mejoras sugeridas

- Sacar `.env`, `datos/` y `__pycache__/` del versionamiento si no deben estar en Git.
- Crear `.env.example` sin secretos reales.
- Agregar pruebas unitarias para:
  - filtrado de noticias
  - lectura de corpus
  - creacion de chunks
  - herramientas del agente
- Agregar manejo de errores mas explicito para NewsAPI.
- Agregar una seccion de instalacion y uso mas corta dentro de la propia interfaz.
- Separar estilos CSS de `app.py` para reducir el tamano del archivo.
- Agregar logs o trazabilidad de consultas.
- Validar que el vectorstore exista antes de inicializar el agente.

## Comandos utiles

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Descargar noticias:

```bash
python3 obtener_noticias.py
```

Crear base vectorial:

```bash
python3 crear_vectorstore.py
```

Ejecutar app:

```bash
streamlit run app.py
```

Evaluar agente:

```bash
python3 evaluacion.py
```

Ver estado de Git:

```bash
git status --short --branch
```
