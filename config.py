"""Configuracion central del enfoque RAG de NewsAgent."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "datos"
NEWS_JSON = DATA_DIR / "noticias.json"
NEWS_TXT = DATA_DIR / "noticias.txt"
CORPUS_METADATA = DATA_DIR / "metadata_corpus.json"
VECTORSTORE_DIR = DATA_DIR / "noticias_db"

ENFOQUE_AGENTE = (
    "politica colombiana actual, con foco en elecciones presidenciales 2026, "
    "candidatos, encuestas, partidos, coaliciones, instituciones electorales, "
    "gobierno, oposicion, seguridad electoral y riesgos democraticos"
)

DIAS_BUSQUEDA = 28
PAGINAS_POR_TEMA = 1
MAX_SOLICITUDES_POR_EJECUCION = 80
MAX_ARTICULOS_RSS_POR_TEMA = 150
MIN_NOTICIAS_OBJETIVO = 1500

NEWSAPI_DOMINIOS_PRIORITARIOS = []
NEWSAPI_DOMINIOS_EXCLUIDOS = [
    "rt.com",
    "latercera.com",
    "lanacion.com.ar",
    "nacion.com",
    "abc.es",
    "jornada.com.mx",
    "elmundo.es",
    "elespanol.com",
    "elpais.com.uy",
]

FUENTES_RSS = [
    {
        "nombre": "El Tiempo - Politica y Gobierno",
        "url": "https://www.eltiempo.com/rss/politica_gobierno.xml",
        "tipo": "feed",
    },
    {
        "nombre": "El Tiempo - Colombia",
        "url": "https://www.eltiempo.com/rss/colombia.xml",
        "tipo": "feed",
    },
    {
        "nombre": "El Tiempo - Justicia",
        "url": "https://www.eltiempo.com/rss/justicia.xml",
        "tipo": "feed",
    },
    {
        "nombre": "El Tiempo - Bogota",
        "url": "https://www.eltiempo.com/rss/bogota.xml",
        "tipo": "feed",
    },
    {
        "nombre": "Google News Colombia",
        "url": "https://news.google.com/rss/search?q={query}&hl=es-419&gl=CO&ceid=CO:es-419",
        "tipo": "busqueda",
    },
]

CATEGORIAS_TEMAS = {
    "Actualidad politica nacional": [
        "Colombia AND (politica OR política OR gobierno OR congreso OR Petro)",
        "Colombia AND (oposicion OR oposición OR coalicion OR coalición OR partidos)",
        "Colombia AND (crisis OR debate OR reforma OR gabinete) AND politica",
        "Colombia AND (Corte OR Fiscalia OR Fiscalía OR Procuraduria OR Procuraduría) AND politica",
    ],
    "Elecciones presidenciales Colombia 2026": [
        "elecciones presidenciales Colombia 2026",
        "campaña presidencial Colombia 2026",
        "precandidatos presidenciales Colombia 2026",
        "candidatos presidenciales Colombia",
        "presidenciales Colombia 2026",
        "primera vuelta presidencial Colombia 2026",
        "segunda vuelta presidencial Colombia 2026",
        "elecciones 2026 Colombia presidente",
        "consulta presidencial Colombia 2026",
        "campaña electoral Colombia 2026",
    ],
    "Candidatos y propuestas": [
        "propuestas candidatos presidenciales Colombia",
        "programa de gobierno candidatos Colombia 2026",
        "debate candidatos presidenciales Colombia",
        "aspirantes presidenciales Colombia",
        "candidaturas Colombia 2026",
        "hojas de vida candidatos presidenciales Colombia",
        "alianzas candidatos presidenciales Colombia",
        "precandidatos Colombia propuestas",
    ],
    "Encuestas y opinion publica": [
        "encuesta presidencial Colombia 2026",
        "intencion de voto Colombia presidenciales",
        "favorabilidad candidatos Colombia",
        "opinion publica Colombia elecciones",
        "sondeo presidencial Colombia",
        "tracking electoral Colombia",
        "imagen candidatos presidenciales Colombia",
        "opinión pública gobierno Petro Colombia",
    ],
    "Partidos, coaliciones y Congreso": [
        "Colombia AND (partidos OR coaliciones OR bancada OR Congreso)",
        "Colombia AND (Senado OR Camara OR Cámara OR congresistas)",
        "Pacto Historico elecciones 2026 Colombia",
        "Centro Democratico elecciones 2026 Colombia",
        "Partido Liberal elecciones 2026 Colombia",
        "Partido Conservador elecciones 2026 Colombia",
        "Alianza Verde elecciones 2026 Colombia",
        "Congreso Colombia elecciones presidenciales",
        "oposicion Colombia elecciones 2026",
        "reforma politica Congreso Colombia",
        "elecciones Congreso Colombia 2026",
    ],
    "Instituciones y reglas electorales": [
        "Registraduria elecciones Colombia 2026",
        "Consejo Nacional Electoral Colombia elecciones",
        "CNE Colombia candidatos presidenciales",
        "financiacion campañas Colombia",
        "calendario electoral Colombia 2026",
        "inscripcion candidatos presidenciales Colombia",
        "reforma politica Colombia elecciones",
        "garantias electorales Colombia",
        "delitos electorales Colombia CNE",
    ],
    "Gobierno y contexto politico": [
        "Colombia AND Petro AND (gobierno OR reforma OR Congreso)",
        "Colombia AND (reforma salud OR reforma laboral OR reforma pensional)",
        "Colombia AND gobierno AND (crisis OR gabinete OR ministros)",
        "Colombia AND (paz total OR seguridad OR orden publico)",
        "gabinete Colombia Petro politica",
        "relacion gobierno Congreso Colombia",
        "oposicion gobierno Petro Colombia",
        "debate politico Colombia actualidad",
        "Corte Constitucional Colombia politica",
        "Fiscalia Colombia politica",
        "Procuraduria Colombia politica",
        "reforma salud Colombia gobierno",
        "reforma laboral Colombia gobierno",
        "reforma pensional Colombia gobierno",
        "paz total Colombia gobierno",
    ],
    "Seguridad y riesgos electorales": [
        "Colombia AND (seguridad electoral OR violencia politica OR riesgo electoral)",
        "Colombia AND (desinformacion OR desinformación OR delitos electorales)",
        "Colombia AND (orden publico OR orden público) AND elecciones",
        "MOE Colombia elecciones 2026",
        "compra de votos Colombia elecciones",
    ],
    "Ampliacion de cobertura politica": [
        "Gustavo Petro Colombia mayo 2026",
        "Congreso Colombia reformas gobierno Petro",
        "Corte Constitucional Colombia gobierno Petro",
        "Fiscalia Colombia gobierno politica",
        "Consejo Nacional Electoral sanciones Colombia",
        "Registraduria puestos votacion Colombia 2026",
        "Pacto Historico consulta presidencial 2026",
        "Centro Democratico candidato presidencial 2026",
        "Partido Liberal candidato presidencial 2026",
        "Partido Conservador candidato presidencial 2026",
        "Alianza Verde candidato presidencial 2026",
        "Claudia Lopez presidencial Colombia 2026",
        "Vicky Davila presidencial Colombia 2026",
        "Sergio Fajardo presidencial Colombia 2026",
        "Ivan Cepeda presidencial Colombia 2026",
        "Paloma Valencia presidencial Colombia 2026",
        "Maria Fernanda Cabal presidencial Colombia 2026",
        "Abelardo De La Espriella presidencial Colombia 2026",
        "Daniel Quintero presidencial Colombia 2026",
        "Gustavo Bolivar presidencial Colombia 2026",
        "Roy Barreras presidencial Colombia 2026",
        "Juan Manuel Galan presidencial Colombia 2026",
        "Miguel Uribe elecciones Colombia 2026",
        "encuestas Invamer presidencial Colombia",
        "encuestas Guarumo presidencial Colombia",
        "encuestas CNC presidencial Colombia",
        "debate presidencial Colombia candidatos",
        "alianzas politicas Colombia presidenciales",
        "financiacion campañas presidenciales Colombia",
        "desinformacion electoral Colombia redes sociales",
    ],
}

TEMAS = [tema for temas in CATEGORIAS_TEMAS.values() for tema in temas]

PALABRAS_COLOMBIA = [
    "colombia",
    "colombiano",
    "colombiana",
    "colombianos",
    "colombianas",
    "bogota",
    "bogotá",
    "petro",
    "registraduria",
    "registraduría",
    "cne",
    "consejo nacional electoral",
]

PALABRAS_POLITICA_ELECTORAL = [
    "eleccion",
    "elección",
    "elecciones",
    "electoral",
    "presidencial",
    "presidenciales",
    "presidente",
    "candidato",
    "candidata",
    "candidatos",
    "precandidato",
    "precandidata",
    "campaña",
    "campana",
    "voto",
    "votacion",
    "votación",
    "encuesta",
    "sondeo",
    "intencion de voto",
    "intención de voto",
    "favorabilidad",
    "partido",
    "coalicion",
    "coalición",
    "alianza",
    "oposicion",
    "oposición",
    "congreso",
    "senado",
    "camara",
    "cámara",
    "gobierno",
    "ministro",
    "ministra",
    "reforma",
    "politica",
    "política",
    "debate",
    "propuesta",
    "programa",
    "moe",
    "garantias electorales",
    "garantías electorales",
    "desinformacion",
    "desinformación",
    "delitos electorales",
]
