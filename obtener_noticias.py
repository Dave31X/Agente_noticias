# obtener_noticias.py
import requests
import json
import os
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")

# ── TEMAS: Finanzas, Economía, Gobierno y Política ─────────────
TEMAS = [

    # ── ECONOMÍA COLOMBIA ──────────────────────────────────────
    "economía Colombia 2025",
    "inflación Colombia",
    "dólar peso colombiano",
    "PIB Colombia crecimiento",
    "desempleo Colombia",
    "pobreza Colombia índice",
    "exportaciones importaciones Colombia",
    "petróleo Colombia barril",
    "minería Colombia producción",
    "café Colombia precios",
    "deuda pública Colombia",
    "déficit fiscal Colombia",
    "inversión extranjera Colombia",
    "comercio exterior Colombia",

    # ── FINANZAS COLOMBIA ──────────────────────────────────────
    "Banco de la República Colombia",
    "tasas de interés Colombia",
    "bolsa valores Colombia BVC",
    "bancos Colombia sector financiero",
    "crédito hipotecario Colombia",
    "reforma pensional Colombia",
    "reforma tributaria Colombia",
    "presupuesto nacional Colombia",
    "Hacienda Colombia ministerio",
    "finanzas públicas Colombia",
    "criptomonedas Colombia regulación",
    "seguros Colombia mercado",
    "Fondo Monetario Colombia",

    # ── GOBIERNO COLOMBIA ──────────────────────────────────────
    "Gustavo Petro gobierno",
    "Petro presidente Colombia",
    "gobierno Colombia 2025 decisiones",
    "ministerio Colombia decreto",
    "Casa de Nariño Colombia",
    "vicepresidente Colombia Francia Márquez",
    "gabinete Colombia ministros",
    "decreto ley Colombia",
    "política pública Colombia",
    "gasto público Colombia gobierno",
    "contratos estado Colombia",
    "corrupción Colombia gobierno",
    "Plan Nacional Desarrollo Colombia",
    "Colombia reformas gobierno Petro",

    # ── POLÍTICA COLOMBIA ──────────────────────────────────────
    "congreso Colombia senado cámara",
    "elecciones Colombia 2026",
    "partidos políticos Colombia",
    "oposición Colombia congreso",
    "reforma Colombia debate",
    "Gustavo Petro reforma laboral",
    "reforma salud Colombia",
    "reforma educación Colombia",
    "politica colombiana debate",
    "alcalde Bogotá Carlos Fernando Galán",
    "gobernadores Colombia",
    "plebiscito referendo Colombia",
    "Corte Constitucional Colombia",
    "Procuraduría Colombia",
    "Fiscalía Colombia",

    # ── ECONOMÍA LATINOAMÉRICA ─────────────────────────────────
    "economía América Latina 2025",
    "Venezuela economía crisis",
    "Ecuador economía gobierno",
    "Argentina economía Milei",
    "Chile economía gobierno",
    "Brasil economía Lula",
    "México economía gobierno",
    "Perú economía política",
    "LATAM mercados emergentes",
    "dólar América Latina",

    # ── FINANZAS GLOBALES ──────────────────────────────────────
    "Reserva Federal tasas interés",
    "Banco Central Europeo política monetaria",
    "inflación mundial 2025",
    "recesión economía global",
    "mercados financieros globales",
    "petróleo precio barril mundial",
    "oro precio mercados",
    "criptomonedas Bitcoin mercado",
    "Wall Street mercados",
    "economía China crecimiento",
    "guerra comercial aranceles",
    "FMI Banco Mundial economía",
    "deuda global países",
    "tipo de cambio divisas",

    # ── POLÍTICA INTERNACIONAL ─────────────────────────────────
    "Colombia Estados Unidos relaciones",
    "Colombia Venezuela relaciones",
    "Colombia OEA Naciones Unidas",
    "geopolítica América Latina",
    "Trump política exterior",
    "Unión Europea política",
    "China política gobierno",
    "Rusia Ucrania guerra economía",
    "OTAN geopolítica",
    "elecciones mundo 2025",
]

PAGINAS_POR_TEMA = 2  # 2 páginas × 100 artículos = hasta 200 por tema

def obtener_articulos_pagina(tema, pagina=1, cantidad=100):
    """Descarga una página de artículos de NewsAPI"""
    fecha_inicio = (datetime.now() - timedelta(days=29)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": tema,
        "language": "es",
        "from": fecha_inicio,
        "sortBy": "relevancy",
        "pageSize": cantidad,
        "page": pagina,
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
    Filtra noticias que realmente sean sobre economía,
    finanzas, gobierno o política.
    """
    palabras_clave = [
        # Economía
        "economía", "económico", "pib", "inflación", "deflación",
        "desempleo", "empleo", "exportación", "importación", "comercio",
        "petróleo", "minería", "producción", "mercado", "precio",
        "crecimiento", "recesión", "inversión", "deuda", "déficit",
        # Finanzas
        "banco", "tasa", "interés", "bolsa", "acciones", "dólar",
        "peso", "moneda", "crédito", "préstamo", "pensión", "tributario",
        "impuesto", "presupuesto", "hacienda", "financiero", "fiscal",
        "bitcoin", "criptomoneda", "fondo", "divisa", "cambio",
        # Gobierno
        "gobierno", "ministro", "presidente", "decreto", "ley",
        "reforma", "política pública", "congreso", "senado", "cámara",
        "gobernador", "alcalde", "estado", "nación", "república",
        # Política
        "partido", "elección", "candidato", "campaña", "voto",
        "petro", "oposición", "coalición", "debate", "propuesta",
        "corte", "tribunal", "ley", "constitución", "regulación",
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

    categorias = {
        "Economía Colombia": TEMAS[:14],
        "Finanzas Colombia": TEMAS[14:27],
        "Gobierno Colombia": TEMAS[27:41],
        "Política Colombia": TEMAS[41:56],
        "Economía LATAM": TEMAS[56:65],
        "Finanzas Globales": TEMAS[65:79],
        "Política Internacional": TEMAS[79:],
    }

    for categoria, temas in categorias.items():
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
    print("🚀 Descarga focalizada: Economía · Finanzas · Gobierno · Política")
    print(f"📋 Total de temas: {len(TEMAS)}")
    print(f"📄 Páginas por tema: {PAGINAS_POR_TEMA} (hasta {PAGINAS_POR_TEMA * 100} art/tema)\n")
    inicio = time.time()
    noticias = descargar_todas()
    guardar(noticias)
    mins = (time.time() - inicio) / 60
    print(f"\n⏱️  Tiempo total: {mins:.1f} minutos")
    print(f"🎉 {len(noticias)} noticias únicas y relevantes listas para RAG")