# obtener_noticias.py
import requests
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from html import unescape
from dotenv import load_dotenv
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from config import (
    CATEGORIAS_TEMAS,
    CORPUS_METADATA,
    DATA_DIR,
    DIAS_BUSQUEDA,
    FUENTES_RSS,
    MAX_ARTICULOS_RSS_POR_TEMA,
    MIN_NOTICIAS_OBJETIVO,
    NEWSAPI_DOMINIOS_EXCLUIDOS,
    MAX_SOLICITUDES_POR_EJECUCION,
    NEWSAPI_DOMINIOS_PRIORITARIOS,
    NEWS_JSON,
    NEWS_TXT,
    PAGINAS_POR_TEMA,
    PALABRAS_COLOMBIA,
    PALABRAS_POLITICA_ELECTORAL,
    TEMAS,
)

load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")
_RSS_CACHE = {}


class NewsAPIRateLimitError(RuntimeError):
    """Señal interna para guardar el corpus parcial y terminar sin bucles de espera."""


class NewsAPIUnavailableError(RuntimeError):
    """NewsAPI no esta disponible para esta ejecucion; se debe usar fallback."""


def construir_query(tema):
    """Consulta simple: NewsAPI no siempre interpreta bien AND + comillas."""
    if " AND " in tema or " OR " in tema:
        return tema
    if "colombia" in tema.lower():
        return tema
    return f"{tema} Colombia"


def limpiar_query_rss(tema):
    """Google News RSS funciona mejor con una busqueda menos booleana."""
    reemplazos = {
        " AND ": " ",
        " OR ": " ",
        "(": " ",
        ")": " ",
        '"': " ",
    }
    query = tema
    for viejo, nuevo in reemplazos.items():
        query = query.replace(viejo, nuevo)
    query = " ".join(query.split())
    if "colombia" not in query.lower():
        query = f"{query} Colombia"
    return query


def fecha_rss_a_iso(fecha):
    try:
        return parsedate_to_datetime(fecha).date().isoformat()
    except Exception:
        return datetime.now().date().isoformat()


def obtener_articulos_pagina(tema, categoria, pagina=1, cantidad=100):
    """Descarga una página de artículos de NewsAPI"""
    fecha_inicio = (datetime.now() - timedelta(days=DIAS_BUSQUEDA)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": construir_query(tema),
        "language": "es",
        "from": fecha_inicio,
        "sortBy": "publishedAt",
        "pageSize": cantidad,
        "page": pagina,
        "searchIn": "title,description,content",
        "apiKey": API_KEY,
    }
    if NEWSAPI_DOMINIOS_PRIORITARIOS:
        params["domains"] = ",".join(NEWSAPI_DOMINIOS_PRIORITARIOS)
    if NEWSAPI_DOMINIOS_EXCLUIDOS:
        params["excludeDomains"] = ",".join(NEWSAPI_DOMINIOS_EXCLUIDOS)
    try:
        r = requests.get(url, params=params, timeout=12)
        if r.status_code in (401, 403):
            raise NewsAPIUnavailableError(
                f"NewsAPI rechazo la solicitud ({r.status_code}). Revisa clave, plan o restricciones."
            )
        if r.status_code == 429:
            raise NewsAPIRateLimitError(
                "NewsAPI alcanzo el limite de solicitudes de tu plan. "
                "Se usara una fuente RSS de respaldo."
            )
        r.raise_for_status()
        datos = r.json()
        if datos.get("status") == "ok":
            return [
                {
                    "titulo": a["title"],
                    "descripcion": a.get("description", ""),
                    "contenido_parcial": a.get("content", ""),
                    "fuente": a["source"]["name"],
                    "fecha": a["publishedAt"][:10],
                    "categoria": categoria,
                    "tema": tema,
                    "url": a["url"],
                    "origen_ingesta": "newsapi",
                }
                for a in datos["articles"]
                if a.get("title")
                and a.get("title") != "[Removed]"
                and a.get("description")
                and len(a.get("description", "")) > 50
            ]
        elif datos.get("code") == "rateLimited":
            raise NewsAPIRateLimitError(
                "NewsAPI alcanzo el limite de solicitudes de tu plan. "
                "Se usara una fuente RSS de respaldo."
            )
        elif datos.get("code") == "maximumResultsReached":
            return []
        else:
            print(f"   ⚠️ NewsAPI: {datos.get('code', 'sin_codigo')} - {datos.get('message', 'sin mensaje')}")
    except NewsAPIRateLimitError:
        raise
    except NewsAPIUnavailableError:
        raise
    except requests.exceptions.RequestException as e:
        raise NewsAPIUnavailableError(
            f"NewsAPI no respondio correctamente ({e.__class__.__name__}). Se usara RSS de respaldo."
        ) from e
    except Exception as e:
        print(f"   ❌ Error procesando NewsAPI: {e.__class__.__name__}")
    return []


def limpiar_html_basico(texto):
    """Limpieza liviana para descripciones RSS sin agregar dependencias."""
    texto = unescape(texto or "")
    partes = []
    dentro_etiqueta = False
    for caracter in texto:
        if caracter == "<":
            dentro_etiqueta = True
            partes.append(" ")
        elif caracter == ">":
            dentro_etiqueta = False
            partes.append(" ")
        elif not dentro_etiqueta:
            partes.append(caracter)
    return " ".join("".join(partes).split())


def obtener_articulos_rss(tema, categoria):
    """Fallback sin clave: consulta feeds RSS y normaliza al formato del corpus."""
    articulos_busqueda = []
    articulos_feed = []
    query = limpiar_query_rss(tema)

    for fuente_rss in FUENTES_RSS:
        articulos_fuente = []
        plantilla_url = fuente_rss["url"]
        url = plantilla_url.format(query=quote_plus(query)) if "{query}" in plantilla_url else plantilla_url
        try:
            if url not in _RSS_CACHE:
                r = requests.get(
                    url,
                    timeout=12,
                    headers={"User-Agent": "NewsAgent/1.0 (+https://local)"},
                )
                r.raise_for_status()
                _RSS_CACHE[url] = r.content
            raiz = ET.fromstring(_RSS_CACHE[url])
        except Exception as e:
            print(f"   ⚠️ RSS {fuente_rss.get('nombre', 'sin_nombre')}: {e}")
            continue

        for item in raiz.findall(".//item"):
            titulo = (item.findtext("title") or "").strip()
            enlace = (item.findtext("link") or "").strip()
            descripcion = limpiar_html_basico(item.findtext("description") or "")
            fecha = fecha_rss_a_iso(item.findtext("pubDate") or "")
            fuente = item.findtext("source") or fuente_rss.get("nombre", "RSS")

            if not titulo or not enlace:
                continue

            articulos_fuente.append(
                {
                    "titulo": titulo,
                    "descripcion": descripcion,
                    "contenido_parcial": descripcion,
                    "fuente": fuente,
                    "fecha": fecha,
                    "categoria": categoria,
                    "tema": tema,
                    "url": enlace,
                    "origen_ingesta": "rss",
                }
            )

        if fuente_rss.get("tipo") == "busqueda" or "{query}" in plantilla_url:
            articulos_busqueda.extend(articulos_fuente)
        else:
            articulos_feed.append(articulos_fuente)

    mezclados = list(articulos_busqueda)
    max_items = max((len(items) for items in articulos_feed), default=0)
    for indice in range(max_items):
        for items in articulos_feed:
            if indice < len(items):
                mezclados.append(items[indice])
            if len(mezclados) >= MAX_ARTICULOS_RSS_POR_TEMA:
                return mezclados

    return mezclados


def obtener_contenido_completo(noticia):
    """Descarga el artículo completo. Si falla, usa lo que tiene NewsAPI."""
    if noticia.get("origen_ingesta") == "rss":
        return construir_contenido_fallback(noticia)

    try:
        from newspaper import Article
        art = Article(noticia["url"], language="es")
        art.download()
        art.parse()
        if art.text and len(art.text) > 150:
            return art.text[:8000]  # máximo 8000 chars por artículo
    except Exception:
        pass

    return construir_contenido_fallback(noticia)


def construir_contenido_fallback(noticia):
    """Texto suficiente para indexar fuentes que solo entregan metadata/resumen."""
    parcial = (noticia.get("contenido_parcial", "") or "").split("[+")[0].strip()
    partes = [
        noticia.get("titulo", ""),
        noticia.get("descripcion", ""),
        parcial,
        f"Categoria: {noticia.get('categoria', '')}",
        f"Tema: {noticia.get('tema', '')}",
        f"Fuente: {noticia.get('fuente', '')}",
    ]
    return " ".join(" ".join(p for p in partes if p).split()).strip()


def puntuar_relevancia(noticia):
    """
    Puntua afinidad con el enfoque. Exige senal de Colombia y senal politica/electoral.
    Evita que una noticia economica regional entre solo por mencionar Colombia.
    """
    texto = (
        (noticia.get("titulo") or "") + " " +
        (noticia.get("descripcion") or "") + " " +
        (noticia.get("contenido_parcial") or "")
    ).lower()

    senales_colombia = sum(1 for p in PALABRAS_COLOMBIA if p in texto)
    senales_politica = sum(1 for p in PALABRAS_POLITICA_ELECTORAL if p in texto)
    if senales_colombia == 0 or senales_politica == 0:
        return 0
    return (senales_colombia * 2) + senales_politica


def es_relevante(noticia):
    return puntuar_relevancia(noticia) >= 4


def descargar_todas():
    todas = []
    urls_vistas = set()
    solicitudes = 0
    usar_newsapi = bool(API_KEY)
    if usar_newsapi:
        print("ℹ️ Usaré NewsAPI como fuente principal; RSS queda como respaldo.")
    else:
        print("⚠️ Falta NEWS_API_KEY en .env. Usaré RSS como fuente de respaldo.")

    for categoria, temas in CATEGORIAS_TEMAS.items():
        print(f"\n{'='*55}")
        print(f"📂 {categoria} ({len(temas)} temas)")
        print(f"{'='*55}")

        for i, tema in enumerate(temas):
            print(f"\n  [{i+1}/{len(temas)}] 📡 {tema}")

            paginas = range(1, PAGINAS_POR_TEMA + 1) if usar_newsapi else range(1, 2)
            for pagina in paginas:
                if solicitudes >= MAX_SOLICITUDES_POR_EJECUCION:
                    print(
                        f"\n  ⏹️ Límite local de {MAX_SOLICITUDES_POR_EJECUCION} "
                        "solicitudes alcanzado para cuidar la cuota."
                    )
                    return todas

                try:
                    if usar_newsapi:
                        articulos = obtener_articulos_pagina(tema, categoria, pagina=pagina, cantidad=100)
                        solicitudes += 1
                    else:
                        articulos = obtener_articulos_rss(tema, categoria)
                except NewsAPIRateLimitError as error:
                    print(f"\n  ⏳ {error}")
                    usar_newsapi = False
                    articulos = obtener_articulos_rss(tema, categoria)
                except NewsAPIUnavailableError as error:
                    print(f"\n  ⚠️ {error}")
                    usar_newsapi = False
                    articulos = obtener_articulos_rss(tema, categoria)

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
                    art["relevancia_enfoque"] = puntuar_relevancia(art)
                    todas.append(art)
                    nuevos += 1

                print(f"     Pág {pagina}: {nuevos} nuevas (+{filtrados} filtradas) | Total: {len(todas)}")
                if len(todas) >= MIN_NOTICIAS_OBJETIVO:
                    print(f"\n  ✅ Objetivo de {MIN_NOTICIAS_OBJETIVO} noticias alcanzado.")
                    return todas
                time.sleep(0.4)

    return todas


def guardar(noticias):
    DATA_DIR.mkdir(exist_ok=True)

    # JSON completo
    with open(NEWS_JSON, "w", encoding="utf-8") as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)

    # TXT para RAG — formato optimizado
    with open(NEWS_TXT, "w", encoding="utf-8") as f:
        for i, n in enumerate(noticias):
            f.write(f"=== NOTICIA {i+1} ===\n")
            f.write(f"TITULO: {n['titulo']}\n")
            f.write(f"FUENTE: {n['fuente']}\n")
            f.write(f"FECHA: {n['fecha']}\n")
            f.write(f"CATEGORIA: {n.get('categoria', '')}\n")
            f.write(f"TEMA: {n['tema']}\n")
            f.write(f"DESCRIPCION: {n.get('descripcion', '')}\n")
            f.write(f"CONTENIDO: {n.get('contenido', '')}\n")
            f.write(f"URL: {n.get('url', '')}\n")
            f.write("\n")

    metadata = {
        "generado_en": datetime.now().isoformat(timespec="seconds"),
        "ventana_dias": DIAS_BUSQUEDA,
        "total_noticias": len(noticias),
        "categorias": {},
        "fuentes": {},
        "fecha_min": min((n.get("fecha", "") for n in noticias), default=""),
        "fecha_max": max((n.get("fecha", "") for n in noticias), default=""),
    }

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

    metadata["categorias"] = dict(sorted(cats.items(), key=lambda x: -x[1]))
    metadata["fuentes"] = dict(sorted(fuentes.items(), key=lambda x: -x[1])[:20])
    with open(CORPUS_METADATA, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n📊 Por categoría:")
    for c, cnt in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"   {c}: {cnt}")

    print("\n📰 Top 10 fuentes:")
    for f, cnt in sorted(fuentes.items(), key=lambda x: -x[1])[:10]:
        print(f"   {f}: {cnt}")

    tam = os.path.getsize(NEWS_TXT) / 1024 / 1024
    print(f"\n💾 Tamaño del corpus: {tam:.1f} MB")


if __name__ == "__main__":
    print("🚀 Descarga focalizada: Política Colombia · Presidenciales 2026")
    print(f"📋 Total de temas: {len(TEMAS)}")
    print(f"🗓️  Ventana de búsqueda: últimos {DIAS_BUSQUEDA} días")
    print(f"📄 Páginas por tema: {PAGINAS_POR_TEMA} (hasta {PAGINAS_POR_TEMA * 100} art/tema)\n")
    inicio = time.time()
    noticias = descargar_todas()
    if not noticias:
        print("\n⚠️ No se descargaron noticias.")
        print("   Posibles causas: cuota agotada de NewsAPI, clave inválida o filtros sin resultados.")
        print("   No se sobrescribirá el corpus con una base vacía.")
        sys.exit(1)

    guardar(noticias)
    mins = (time.time() - inicio) / 60
    print(f"\n⏱️  Tiempo total: {mins:.1f} minutos")
    print(f"🎉 {len(noticias)} noticias únicas y relevantes listas para RAG")
