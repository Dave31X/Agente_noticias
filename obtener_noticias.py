# obtener_noticias.py
import requests
import json
import os
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")

# ── ENFOQUE: Política actual de Colombia y presidenciales 2026 ─
CATEGORIAS_TEMAS = {
    "Elecciones presidenciales Colombia 2026": [
        "elecciones presidenciales Colombia 2026",
        "campaña presidencial Colombia 2026",
        "precandidatos presidenciales Colombia 2026",
        "candidatos presidenciales Colombia",
        "presidenciales Colombia 2026",
        "primera vuelta presidencial Colombia 2026",
        "segunda vuelta presidencial Colombia 2026",
        "elecciones 2026 Colombia presidente",
    ],
    "Candidatos y propuestas": [
        "propuestas candidatos presidenciales Colombia",
        "programa de gobierno candidatos Colombia 2026",
        "debate candidatos presidenciales Colombia",
        "aspirantes presidenciales Colombia",
        "candidaturas Colombia 2026",
        "hojas de vida candidatos presidenciales Colombia",
        "alianzas candidatos presidenciales Colombia",
    ],
    "Encuestas y opinion publica": [
        "encuesta presidencial Colombia 2026",
        "intencion de voto Colombia presidenciales",
        "favorabilidad candidatos Colombia",
        "opinion publica Colombia elecciones",
        "sondeo presidencial Colombia",
        "tracking electoral Colombia",
        "imagen candidatos presidenciales Colombia",
    ],
    "Partidos, coaliciones y Congreso": [
        "partidos politicos Colombia elecciones 2026",
        "coaliciones politicas Colombia 2026",
        "Pacto Historico elecciones 2026 Colombia",
        "Centro Democratico elecciones 2026 Colombia",
        "Partido Liberal elecciones 2026 Colombia",
        "Partido Conservador elecciones 2026 Colombia",
        "Alianza Verde elecciones 2026 Colombia",
        "Congreso Colombia elecciones presidenciales",
        "oposicion Colombia elecciones 2026",
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
    ],
    "Gobierno y contexto politico": [
        "Gobierno Petro elecciones 2026",
        "Gustavo Petro politica Colombia actualidad",
        "reformas gobierno Petro elecciones",
        "crisis politica Colombia gobierno",
        "gabinete Colombia Petro politica",
        "relacion gobierno Congreso Colombia",
        "oposicion gobierno Petro Colombia",
        "debate politico Colombia actualidad",
        "Corte Constitucional Colombia politica",
        "Fiscalia Colombia politica",
        "Procuraduria Colombia politica",
    ],
    "Seguridad y riesgos electorales": [
        "seguridad electoral Colombia 2026",
        "violencia politica Colombia elecciones",
        "riesgo electoral Colombia",
        "MOE Colombia elecciones 2026",
        "orden publico elecciones Colombia",
        "desinformacion elecciones Colombia",
        "delitos electorales Colombia",
        "compra de votos Colombia elecciones",
    ],
}

TEMAS = [tema for temas in CATEGORIAS_TEMAS.values() for tema in temas]

DIAS_BUSQUEDA = 30
PAGINAS_POR_TEMA = 2  # 2 paginas x 100 articulos = hasta 200 por tema

def obtener_articulos_pagina(tema, pagina=1, cantidad=100):
    """Descarga una página de artículos de NewsAPI"""
    fecha_inicio = (datetime.now() - timedelta(days=DIAS_BUSQUEDA)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": tema,
        "language": "es",
        "from": fecha_inicio,
        "sortBy": "publishedAt",
        "pageSize": cantidad,
        "page": pagina,
        "searchIn": "title,description,content",
        "apiKey": API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=12)
        datos = r.json()
        if datos["status"] == "ok":
            return [
                {
                    "titulo": a["title"],
                    "descripcion": a.get("description", ""),
                    "contenido_parcial": a.get("content", ""),
                    "fuente": a["source"]["name"],
                    "fecha": a["publishedAt"][:10],
                    "tema": tema,
                    "url": a["url"]
                }
                for a in datos["articles"]
                if a.get("title")
                and a.get("title") != "[Removed]"
                and a.get("description")
                and len(a.get("description", "")) > 50
            ]
        elif datos.get("code") == "rateLimited":
            print("   ⏳ Rate limit — esperando 60s...")
            time.sleep(60)
        elif datos.get("code") == "maximumResultsReached":
            return []
    except Exception as e:
        print(f"   ❌ Error conexión: {e}")
    return []

def obtener_contenido_completo(noticia):
    """Descarga el artículo completo. Si falla, usa lo que tiene NewsAPI."""
    try:
        from newspaper import Article
        art = Article(noticia["url"], language="es")
        art.download()
        art.parse()
        if art.text and len(art.text) > 150:
            return art.text[:8000]  # máximo 8000 chars por artículo
    except:
        pass

    # Fallback: descripción + contenido parcial limpio
    contenido = noticia.get("descripcion", "")
    parcial = noticia.get("contenido_parcial", "")
    if parcial:
        # Eliminar el truncamiento "[+XXXX chars]"
        parcial_limpio = parcial.split("[+")[0].strip()
        if parcial_limpio:
            contenido += " " + parcial_limpio
    return contenido.strip()

def es_relevante(noticia):
    """
    Filtra noticias que realmente sean sobre politica colombiana,
    elecciones presidenciales y contexto electoral.
    """
    palabras_clave = [
        # Elecciones presidenciales
        "elección", "elecciones", "electoral", "presidencial",
        "presidenciales", "presidente", "candidato", "candidata",
        "candidatos", "precandidato", "precandidata", "campaña",
        "voto", "votación", "segunda vuelta", "primera vuelta",
        "encuesta", "sondeo", "intención de voto", "favorabilidad",
        # Partidos, coaliciones e instituciones
        "partido", "coalición", "alianza", "oposición", "congreso",
        "senado", "cámara", "registraduría", "registraduria",
        "consejo nacional electoral", "cne", "moe", "financiación",
        "financiacion", "garantías electorales", "garantias electorales",
        # Contexto politico nacional
        "gobierno", "petro", "ministro", "ministra", "reforma",
        "política", "politica", "debate", "propuesta", "programa",
        "corte constitucional", "fiscalía", "fiscalia", "procuraduría",
        "procuraduria", "corrupción", "corrupcion", "investigación",
        "investigacion", "desinformación", "desinformacion",
        # Ubicacion
        "colombia", "colombiano", "colombiana", "bogotá", "bogota",
    ]
    texto = (
        (noticia.get("titulo") or "") + " " +
        (noticia.get("descripcion") or "") + " " +
        (noticia.get("contenido_parcial") or "")
    ).lower()

    return any(p in texto for p in palabras_clave)

def descargar_todas():
    todas = []
    urls_vistas = set()
    solicitudes = 0
    MAX_SOLICITUDES_POR_HORA = 90  # NewsAPI límite gratuito

    for categoria, temas in CATEGORIAS_TEMAS.items():
        print(f"\n{'='*55}")
        print(f"📂 {categoria} ({len(temas)} temas)")
        print(f"{'='*55}")

        for i, tema in enumerate(temas):
            print(f"\n  [{i+1}/{len(temas)}] 📡 {tema}")

            for pagina in range(1, PAGINAS_POR_TEMA + 1):
                # Control de rate limit
                if solicitudes >= MAX_SOLICITUDES_POR_HORA:
                    print(f"\n  ⏳ Límite de solicitudes alcanzado. Pausa 65s...")
                    time.sleep(65)
                    solicitudes = 0

                articulos = obtener_articulos_pagina(tema, pagina=pagina, cantidad=100)
                solicitudes += 1

                if not articulos:
                    break  # no hay más páginas

                nuevos = 0
                filtrados = 0
                for art in articulos:
                    if art["url"] in urls_vistas:
                        continue
                    if not es_relevante(art):
                        filtrados += 1
                        continue

                    urls_vistas.add(art["url"])
                    contenido = obtener_contenido_completo(art)
                    art["contenido"] = contenido
                    art["categoria"] = categoria
                    todas.append(art)
                    nuevos += 1

                print(f"     Pág {pagina}: {nuevos} nuevas (+{filtrados} filtradas) | Total: {len(todas)}")
                time.sleep(0.4)

    return todas

def guardar(noticias):
    os.makedirs("datos", exist_ok=True)

    # JSON completo
    with open("datos/noticias.json", "w", encoding="utf-8") as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)

    # TXT para RAG — formato optimizado
    with open("datos/noticias.txt", "w", encoding="utf-8") as f:
        for i, n in enumerate(noticias):
            f.write(f"=== NOTICIA {i+1} ===\n")
            f.write(f"TITULO: {n['titulo']}\n")
            f.write(f"FUENTE: {n['fuente']}\n")
            f.write(f"FECHA: {n['fecha']}\n")
            f.write(f"CATEGORIA: {n.get('categoria', '')}\n")
            f.write(f"TEMA: {n['tema']}\n")
            f.write(f"DESCRIPCION: {n.get('descripcion', '')}\n")
            f.write(f"CONTENIDO: {n.get('contenido', '')}\n")
            f.write("\n")

    # Resumen detallado
    print(f"\n{'='*55}")
    print(f"✅ TOTAL: {len(noticias)} noticias guardadas")
    print(f"{'='*55}")

    cats = {}
    fuentes = {}
    for n in noticias:
        c = n.get("categoria", "Otro")
        cats[c] = cats.get(c, 0) + 1
        f = n.get("fuente", "?")
        fuentes[f] = fuentes.get(f, 0) + 1

    print("\n📊 Por categoría:")
    for c, cnt in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"   {c}: {cnt}")

    print("\n📰 Top 10 fuentes:")
    for f, cnt in sorted(fuentes.items(), key=lambda x: -x[1])[:10]:
        print(f"   {f}: {cnt}")

    tam = os.path.getsize("datos/noticias.txt") / 1024 / 1024
    print(f"\n💾 Tamaño del corpus: {tam:.1f} MB")

if __name__ == "__main__":
    print("🚀 Descarga focalizada: Política Colombia · Presidenciales 2026")
    print(f"📋 Total de temas: {len(TEMAS)}")
    print(f"🗓️  Ventana de búsqueda: últimos {DIAS_BUSQUEDA} días")
    print(f"📄 Páginas por tema: {PAGINAS_POR_TEMA} (hasta {PAGINAS_POR_TEMA * 100} art/tema)\n")
    inicio = time.time()
    noticias = descargar_todas()
    guardar(noticias)
    mins = (time.time() - inicio) / 60
    print(f"\n⏱️  Tiempo total: {mins:.1f} minutos")
    print(f"🎉 {len(noticias)} noticias únicas y relevantes listas para RAG")
