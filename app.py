# app.py
# Interfaz profesional para NewsAgent Intelligence Platform

import streamlit as st
import json
import os
import html
import importlib.util
from pathlib import Path
from datetime import datetime
from collections import Counter

# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN GENERAL
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NewsAgent | Intelligence Platform",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "datos"
NEWS_JSON = DATA_DIR / "noticias.json"


# ─────────────────────────────────────────────────────────────
# IMPORTAR AGENTE DE FORMA ROBUSTA
# Sirve si tu archivo se llama agente.py o 4_agente.py
# ─────────────────────────────────────────────────────────────
def importar_crear_agente():
    try:
        from agente import crear_agente
        return crear_agente
    except Exception:
        archivo_agente = BASE_DIR / "4_agente.py"
        if archivo_agente.exists():
            spec = importlib.util.spec_from_file_location("agente_modulo", archivo_agente)
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            return modulo.crear_agente
        raise ImportError(
            "No se encontró crear_agente. Verifica que exista agente.py o 4_agente.py "
            "y que dentro esté definida la función crear_agente()."
        )


# ─────────────────────────────────────────────────────────────
# ESTILOS CSS PROFESIONALES
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    :root {
        --bg-primary: #f6f8fb;
        --bg-secondary: #ffffff;
        --bg-sidebar: #0f172a;
        --text-primary: #111827;
        --text-secondary: #64748b;
        --text-muted: #94a3b8;
        --border: #e5e7eb;
        --accent: #2563eb;
        --accent-soft: #dbeafe;
        --success: #16a34a;
        --warning: #d97706;
        --danger: #dc2626;
        --card-shadow: 0 14px 35px rgba(15, 23, 42, 0.08);
    }

    html, body, [class*="css"] {
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .stApp {
        background: var(--bg-primary);
        color: var(--text-primary);
    }

    #MainMenu, footer, header, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
        display: none !important;
    }

    .block-container {
        padding-top: 1.4rem !important;
        padding-bottom: 6rem !important;
        max-width: 1440px !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--bg-sidebar) !important;
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    [data-testid="stSidebar"] * {
        color: #e5e7eb;
    }

    .sidebar-brand {
        padding: 1.2rem 0.3rem 1.2rem 0.3rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 1rem;
    }

    .brand-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .brand-icon {
        width: 42px;
        height: 42px;
        border-radius: 14px;
        background: linear-gradient(135deg, #2563eb 0%, #38bdf8 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 800;
        font-size: 1.1rem;
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.35);
    }

    .brand-title {
        font-size: 1.05rem;
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: -0.02em;
    }

    .brand-subtitle {
        font-size: 0.72rem;
        color: #94a3b8 !important;
        margin-top: 0.15rem;
    }

    .executive-ribbon {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        margin-top: 0.85rem;
        padding: 0.42rem 0.7rem;
        border-radius: 999px;
        background: rgba(37, 99, 235, 0.12);
        border: 1px solid rgba(59, 130, 246, 0.22);
        color: #bfdbfe !important;
        font-size: 0.72rem;
        font-weight: 800;
    }

    .side-section {
        background: rgba(255,255,255,0.035);
        border: 1px solid rgba(255,255,255,0.075);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .side-title {
        font-size: 0.72rem;
        font-weight: 800;
        color: #94a3b8 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.8rem;
    }

    .side-metric {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.58rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }

    .side-metric:last-child {
        border-bottom: none;
    }

    .side-label {
        color: #cbd5e1 !important;
        font-size: 0.82rem;
    }

    .side-value {
        font-weight: 800;
        font-size: 1.05rem;
        color: #ffffff !important;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.4rem 0.65rem;
        background: rgba(22, 163, 74, 0.12);
        border: 1px solid rgba(22, 163, 74, 0.25);
        border-radius: 999px;
        font-size: 0.76rem;
        color: #86efac !important;
        font-weight: 700;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #22c55e;
        box-shadow: 0 0 0 4px rgba(34,197,94,0.15);
    }

    .tag-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
    }

    .topic-tag {
        padding: 0.35rem 0.55rem;
        background: rgba(148, 163, 184, 0.10);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 999px;
        font-size: 0.72rem;
        color: #cbd5e1 !important;
        white-space: nowrap;
    }

    .sidebar-note {
        color: #94a3b8 !important;
        font-size: 0.75rem;
        line-height: 1.55;
    }

    /* Hero */
    .hero-card {
        background: radial-gradient(circle at 85% 15%, rgba(56,189,248,0.26), transparent 28%),
                    linear-gradient(135deg, #0b1120 0%, #172033 48%, #1d4ed8 132%);
        border-radius: 28px;
        padding: 2rem;
        box-shadow: 0 24px 60px rgba(15, 23, 42, 0.20);
        color: white;
        position: relative;
        overflow: hidden;
        margin-bottom: 1.2rem;
    }

    .hero-card::after {
        content: "";
        position: absolute;
        width: 420px;
        height: 420px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(56,189,248,0.22), transparent 70%);
        right: -150px;
        top: -180px;
    }

    .hero-content {
        position: relative;
        z-index: 2;
    }

    .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.38rem 0.72rem;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.20);
        backdrop-filter: blur(12px);
        border-radius: 999px;
        color: #dbeafe !important;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 1.1rem;
    }

    .hero-title {
        font-size: clamp(2rem, 4vw, 3.4rem);
        line-height: 1.02;
        font-weight: 850;
        letter-spacing: -0.055em;
        margin-bottom: 0.85rem;
        max-width: 820px;
    }

    .hero-subtitle {
        color: #cbd5e1 !important;
        font-size: 1.02rem;
        line-height: 1.65;
        max-width: 760px;
    }

    .hero-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.65rem;
        margin-top: 1.3rem;
    }

    .hero-chip {
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 999px;
        padding: 0.5rem 0.8rem;
        font-size: 0.82rem;
        color: #e5e7eb !important;
    }

    /* KPI cards */
    .metric-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(226, 232, 240, 0.95);
        border-radius: 24px;
        padding: 1.25rem;
        box-shadow: 0 14px 34px rgba(15,23,42,0.075);
        min-height: 128px;
    }

    .metric-label {
        color: var(--text-secondary);
        font-size: 0.78rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.6rem;
    }

    .metric-value {
        color: var(--text-primary);
        font-size: 2rem;
        font-weight: 850;
        letter-spacing: -0.04em;
        margin-bottom: 0.25rem;
    }

    .metric-caption {
        color: var(--text-secondary);
        font-size: 0.82rem;
        line-height: 1.45;
    }

    .metric-accent {
        display: inline-flex;
        padding: 0.25rem 0.5rem;
        border-radius: 999px;
        background: var(--accent-soft);
        color: #1d4ed8 !important;
        font-size: 0.72rem;
        font-weight: 800;
        margin-top: 0.55rem;
    }

    /* Panels */
    .panel {
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 1.35rem;
        box-shadow: 0 14px 34px rgba(15,23,42,0.075);
        margin-top: 1rem;
    }

    .panel-title {
        color: var(--text-primary);
        font-size: 1.05rem;
        font-weight: 850;
        letter-spacing: -0.02em;
        margin-bottom: 0.3rem;
    }

    .panel-subtitle {
        color: var(--text-secondary);
        font-size: 0.86rem;
        line-height: 1.5;
        margin-bottom: 1rem;
    }

    .insight-row {
        display: flex;
        gap: 0.8rem;
        padding: 0.8rem 0;
        border-bottom: 1px solid var(--border);
    }

    .insight-row:last-child {
        border-bottom: none;
    }

    .insight-icon {
        width: 36px;
        height: 36px;
        flex: 0 0 36px;
        border-radius: 12px;
        background: var(--accent-soft);
        color: #1d4ed8 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 850;
    }

    .insight-title {
        color: var(--text-primary);
        font-size: 0.9rem;
        font-weight: 800;
        margin-bottom: 0.15rem;
    }

    .insight-text {
        color: var(--text-secondary);
        font-size: 0.82rem;
        line-height: 1.45;
    }

    /* Quick question cards */
    .stButton > button {
        width: 100%;
        min-height: 74px;
        border-radius: 18px !important;
        border: 1px solid var(--border) !important;
        background: white !important;
        color: var(--text-primary) !important;
        box-shadow: 0 6px 18px rgba(15,23,42,0.045) !important;
        text-align: left !important;
        padding: 0.85rem 1rem !important;
        font-weight: 750 !important;
        transition: all 0.18s ease !important;
    }

    .stButton > button:hover {
        border-color: rgba(37, 99, 235, 0.35) !important;
        box-shadow: 0 12px 24px rgba(37,99,235,0.11) !important;
        transform: translateY(-1px);
        color: #1d4ed8 !important;
    }

    /* Chat */
    .chat-shell {
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        border: 1px solid var(--border);
        border-radius: 28px;
        box-shadow: var(--card-shadow);
        padding: 1.25rem;
        margin-top: 1rem;
    }

    .chat-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1rem;
    }

    .chat-title {
        font-size: 1.05rem;
        color: var(--text-primary);
        font-weight: 850;
    }

    .chat-subtitle {
        color: var(--text-secondary);
        font-size: 0.82rem;
        margin-top: 0.1rem;
    }

    .chat-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        border-radius: 999px;
        background: #ecfdf5;
        color: #15803d !important;
        padding: 0.42rem 0.7rem;
        font-size: 0.75rem;
        font-weight: 800;
        white-space: nowrap;
    }

    .message-wrap {
        display: flex;
        margin: 0.8rem 0;
    }

    .message-wrap.user {
        justify-content: flex-end;
    }

    .message-wrap.agent {
        justify-content: flex-start;
    }

    .message-card {
        max-width: min(840px, 92%);
        padding: 1rem 1.1rem;
        border-radius: 18px;
        line-height: 1.65;
        font-size: 0.92rem;
        white-space: pre-wrap;
    }

    .message-card.user {
        background: #2563eb;
        color: white !important;
        border-bottom-right-radius: 6px;
        box-shadow: 0 10px 22px rgba(37,99,235,0.22);
    }

    .message-card.agent {
        background: #f8fafc;
        color: #1f2937 !important;
        border: 1px solid #e2e8f0;
        border-bottom-left-radius: 6px;
    }

    .message-meta {
        font-size: 0.7rem;
        font-weight: 850;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
        opacity: 0.78;
    }

    .thinking-card {
        display: inline-flex;
        align-items: center;
        gap: 0.7rem;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        color: var(--text-secondary) !important;
        border-radius: 999px;
        padding: 0.65rem 0.9rem;
        font-size: 0.82rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }

    .loader {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--accent);
        box-shadow: 16px 0 #93c5fd, 32px 0 #bfdbfe;
        animation: dots 1s infinite linear;
    }

    @keyframes dots {
        0% { box-shadow: 16px 0 #93c5fd, 32px 0 #bfdbfe; }
        33% { box-shadow: 16px 0 var(--accent), 32px 0 #bfdbfe; }
        66% { box-shadow: 16px 0 #93c5fd, 32px 0 var(--accent); }
    }

    [data-testid="stChatInput"] {
        background: transparent !important;
    }

    [data-testid="stChatInput"] textarea {
        background: white !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 18px !important;
        color: var(--text-primary) !important;
        box-shadow: 0 8px 24px rgba(15,23,42,0.08) !important;
        min-height: 52px !important;
        font-size: 0.96rem !important;
        padding: 0.9rem 1rem !important;
    }

    [data-testid="stChatInput"] textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12), 0 8px 24px rgba(15,23,42,0.08) !important;
    }

    [data-testid="stChatInput"] button {
        background: #2563eb !important;
        color: white !important;
        border-radius: 14px !important;
    }

    .empty-state {
        text-align: center;
        padding: 2.4rem 1rem 1.8rem;
        color: var(--text-secondary);
    }

    .empty-icon {
        width: 64px;
        height: 64px;
        margin: 0 auto 1rem;
        border-radius: 22px;
        background: var(--accent-soft);
        color: #1d4ed8 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.7rem;
    }

    .empty-title {
        font-size: 1.35rem;
        font-weight: 850;
        color: var(--text-primary);
        margin-bottom: 0.4rem;
    }

    .empty-text {
        max-width: 680px;
        margin: 0 auto;
        line-height: 1.6;
        font-size: 0.92rem;
    }

    .command-box {
        background: rgba(15,23,42,0.7);
        border: 1px solid rgba(148,163,184,0.22);
        border-radius: 14px;
        padding: 0.75rem 0.85rem;
        font-family: "JetBrains Mono", Consolas, monospace;
        font-size: 0.72rem;
        color: #bfdbfe !important;
        margin-top: 0.65rem;
        line-height: 1.6;
    }

    @media (max-width: 900px) {
        .hero-card { padding: 1.4rem; border-radius: 22px; }
        .chat-header { align-items: flex-start; flex-direction: column; }
        .message-card { max-width: 100%; }
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ─────────────────────────────────────────────────────────────
# CARGA DE DATOS Y ESTADÍSTICAS
# ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def cargar_noticias():
    if not NEWS_JSON.exists():
        return []

    try:
        with open(NEWS_JSON, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def calcular_stats(noticias):
    total = len(noticias)
    fuentes = Counter(n.get("fuente", "Sin fuente") for n in noticias if n.get("fuente"))
    temas = Counter(n.get("tema", "Sin tema") for n in noticias if n.get("tema"))
    fechas = sorted({n.get("fecha") for n in noticias if n.get("fecha")}, reverse=True)

    return {
        "total": total,
        "fuentes_total": len(fuentes),
        "temas_total": len(temas),
        "ultima_fecha": fechas[0] if fechas else "—",
        "top_fuentes": fuentes.most_common(5),
        "top_temas": temas.most_common(8),
    }


noticias = cargar_noticias()
stats = calcular_stats(noticias)


# ─────────────────────────────────────────────────────────────
# ESTADO DE SESIÓN
# ─────────────────────────────────────────────────────────────
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

if "agente_error" not in st.session_state:
    st.session_state.agente_error = None

if "agente" not in st.session_state:
    try:
        crear_agente = importar_crear_agente()
        st.session_state.agente = crear_agente()
    except Exception as error:
        st.session_state.agente = None
        st.session_state.agente_error = str(error)


# ─────────────────────────────────────────────────────────────
# FUNCIONES DE RENDER
# ─────────────────────────────────────────────────────────────
def safe_text(texto):
    return html.escape(str(texto)).replace("\n", "<br>")


def render_message(rol, contenido):
    contenido_seguro = safe_text(contenido)

    if rol == "usuario":
        st.markdown(
            f"""
            <div class="message-wrap user">
                <div class="message-card user">
                    <div class="message-meta">Tú</div>
                    {contenido_seguro}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="message-wrap agent">
                <div class="message-card agent">
                    <div class="message-meta">NewsAgent Intelligence</div>
                    {contenido_seguro}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


def procesar_pregunta(pregunta):
    st.session_state.mensajes.append({"rol": "usuario", "contenido": pregunta})

    if st.session_state.agente is None:
        respuesta = (
            "No pude inicializar el agente. Revisa que el archivo agente.py o 4_agente.py "
            "exista y que tenga la función crear_agente().\n\n"
            f"Detalle técnico: {st.session_state.agente_error}"
        )
    else:
        try:
            respuesta_agente = st.session_state.agente.invoke({"input": pregunta})
            respuesta = respuesta_agente.get("output", "No encontré una respuesta disponible.")
        except Exception as error:
            respuesta = (
                "Ocurrió un error al consultar el agente. Revisa que el vectorstore, las claves API "
                "y las dependencias estén correctamente configuradas.\n\n"
                f"Detalle técnico: {error}"
            )

    st.session_state.mensajes.append({"rol": "agente", "contenido": respuesta})


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-row">
                <div class="brand-icon">N</div>
                <div>
                    <div class="brand-title">NewsAgent</div>
                    <div class="brand-subtitle">Radar Ejecutivo</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    estado_sistema = "Activo" if st.session_state.agente is not None else "Pendiente"
    estado_color = "#86efac" if st.session_state.agente is not None else "#fcd34d"

    st.markdown(
        f"""
        <div class="side-section">
            <div class="side-title">Sala de máquinas</div>
            <div class="status-pill" style="color:{estado_color} !important;">
                <span class="status-dot"></span>
                {estado_sistema}
            </div>
            <div class="sidebar-note" style="margin-top:0.75rem;">
                Motor RAG listo para explicar politica colombiana actual con neutralidad y contexto.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="side-section">
            <div class="side-title">Tablero de control</div>
            <div class="side-metric">
                <span class="side-label">Noticias en la lupa</span>
                <span class="side-value">{stats['total']:,}</span>
            </div>
            <div class="side-metric">
                <span class="side-label">Fuentes que hablan</span>
                <span class="side-value">{stats['fuentes_total']}</span>
            </div>
            <div class="side-metric">
                <span class="side-label">Temas en radar</span>
                <span class="side-value">{stats['temas_total']}</span>
            </div>
            <div class="side-metric">
                <span class="side-label">Última pasada</span>
                <span class="side-value" style="font-size:0.9rem;">{stats['ultima_fecha']}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    temas_html = "".join(
        f"<span class='topic-tag'>{html.escape(tema)} · {cantidad}</span>"
        for tema, cantidad in stats["top_temas"]
    ) or "<span class='topic-tag'>Sin datos</span>"

    st.markdown(
        f"""
        <div class="side-section">
            <div class="side-title">Temas que hacen ruido</div>
            <div class="tag-grid">{temas_html}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    fuentes_html = "".join(
        f"""
        <div class="side-metric">
            <span class="side-label">{html.escape(fuente[:24])}</span>
            <span class="side-value" style="font-size:0.9rem;">{cantidad}</span>
        </div>
        """
        for fuente, cantidad in stats["top_fuentes"]
    ) or "<div class='sidebar-note'>Aún no hay fuentes cargadas.</div>"

    st.markdown(
        f"""
        <div class="side-section">
            <div class="side-title">Quién está hablando</div>
            {fuentes_html}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Botones salvavidas")

    if st.button("🧹 Borrar el tablero"):
        st.session_state.mensajes = []
        st.rerun()

    if st.button("🔄 Refrescar el radar"):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        """
        <div class="side-section">
            <div class="side-title">Recargar munición informativa</div>
            <div class="sidebar-note">
                Cuando el radar electoral se quede con noticias viejas, corre estos comandos y vuelve a tener la base al día.
            </div>
            <div class="command-box">
                python3 obtener_noticias.py<br>
                python3 crear_vectorstore.py<br>
                streamlit run app.py
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────────────────────
# CONTENIDO PRINCIPAL
# ─────────────────────────────────────────────────────────────
fecha_actual = datetime.now().strftime("%d/%m/%Y · %H:%M")

st.markdown(
    f"""
    <div class="hero-card">
        <div class="hero-content">
            <div class="eyebrow">🧠 Radar electoral encendido · {fecha_actual}</div>
            <div class="hero-title">Política colombiana explicada sin ruido.</div>
            <div class="hero-subtitle">
                Esta plataforma sigue elecciones presidenciales, candidatos, encuestas, partidos e instituciones,
                y lo convierte en respuestas neutrales, claras y faciles de entender.
            </div>
            <div class="executive-ribbon">✨ Hechos separados de opiniones · contexto para todos</div>
            <div class="hero-actions">
                <div class="hero-chip">RAG + Vector DB</div>
                <div class="hero-chip">Colombia politica bajo la lupa</div>
                <div class="hero-chip">Elecciones presidenciales 2026</div>
                <div class="hero-chip">{stats['total']:,} noticias listas para analizar con metodo</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Noticias bajo la lupa</div>
            <div class="metric-value">{stats['total']:,}</div>
            <div class="metric-caption">Artículos organizados para consultar sin perderse en el océano informativo.</div>
            <div class="metric-accent">Base documental</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with kpi2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Fuentes que hablan</div>
            <div class="metric-value">{stats['fuentes_total']}</div>
            <div class="metric-caption">Medios detectados para contrastar señales, narrativas y contexto.</div>
            <div class="metric-accent">Cobertura</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with kpi3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Temas en radar</div>
            <div class="metric-value">{stats['temas_total']}</div>
            <div class="metric-caption">Categorías que permiten ordenar la conversación pública sin drama.</div>
            <div class="metric-accent">Taxonomía</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with kpi4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Última barrida</div>
            <div class="metric-value" style="font-size:1.55rem;">{stats['ultima_fecha']}</div>
            <div class="metric-caption">Fecha más reciente encontrada antes de que el radar pida café.</div>
            <div class="metric-accent">Freshness</div>
        </div>
        """,
        unsafe_allow_html=True
    )


left_panel, right_panel = st.columns([1.25, 0.75])

with left_panel:
    st.markdown(
        """
        <div class="panel">
            <div class="panel-title">Preguntas para entrar en calor</div>
            <div class="panel-subtitle">
                Arranca con una pregunta lista o escribe la tuya. El agente hace el trabajo pesado; tú pones el criterio.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    preguntas = [
        "¿Qué está pasando con las elecciones presidenciales en Colombia?",
        "Explícame los principales candidatos o precandidatos sin sesgos.",
        "¿Qué dicen las encuestas y qué límites tienen?",
        "Sepárame hechos, opiniones e interpretaciones del debate político actual.",
        "¿Qué riesgos electorales se están mencionando?",
        "Hazme un resumen sencillo para alguien que no sigue política todos los días.",
    ]

    qcols = st.columns(2)
    for index, pregunta_sugerida in enumerate(preguntas):
        with qcols[index % 2]:
            if st.button(pregunta_sugerida, key=f"quick_question_{index}"):
                st.session_state["pending_question"] = pregunta_sugerida
                st.rerun()

with right_panel:
    st.markdown(
        """
        <div class="panel">
            <div class="panel-title">Manual rápido para no pelear con la IA</div>
            <div class="panel-subtitle">
                Entre mejor preguntes, más ejecutiva será la respuesta. La IA no adivina, pero sí trabaja duro.
            </div>
            <div class="insight-row">
                <div class="insight-icon">1</div>
                <div>
                    <div class="insight-title">Pide explicacion sencilla</div>
                    <div class="insight-text">Ejemplo: “explicalo para alguien que no sigue politica todos los dias”.</div>
                </div>
            </div>
            <div class="insight-row">
                <div class="insight-icon">2</div>
                <div>
                    <div class="insight-title">Pide separar hechos y opiniones</div>
                    <div class="insight-text">Sirve para no confundir datos confirmados con lecturas de medios o campañas.</div>
                </div>
            </div>
            <div class="insight-row">
                <div class="insight-icon">3</div>
                <div>
                    <div class="insight-title">Pregunta por contexto</div>
                    <div class="insight-text">Pide antecedentes, actores involucrados, posibles efectos y temas pendientes.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="chat-shell">
        <div class="chat-header">
            <div>
                <div class="chat-title">Analista de bolsillo</div>
                <div class="chat-subtitle">Pregunta sobre elecciones, candidatos, encuestas, partidos, gobierno y oposicion.</div>
            </div>
            <div class="chat-badge">● Disponible</div>
        </div>
    """,
    unsafe_allow_html=True
)

if not st.session_state.mensajes:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-icon">💬</div>
            <div class="empty-title">Abre el radar y pregunta sin miedo</div>
            <div class="empty-text">
                El agente responde con base en las noticias indexadas. Para mejores resultados, pide una explicacion sencilla,
                neutral y separada entre hechos, opiniones e implicaciones.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    for mensaje in st.session_state.mensajes:
        render_message(mensaje["rol"], mensaje["contenido"])

st.markdown("</div>", unsafe_allow_html=True)


# Procesar pregunta sugerida
if "pending_question" in st.session_state:
    pregunta_pendiente = st.session_state.pop("pending_question")
    with st.spinner("Analizando la base de noticias..."):
        procesar_pregunta(pregunta_pendiente)
    st.rerun()


# Input principal
pregunta_usuario = st.chat_input("Pregunta algo serio… o algo urgente con pinta de serio")

if pregunta_usuario:
    with st.spinner("Procesando consulta con el agente..."):
        procesar_pregunta(pregunta_usuario)
    st.rerun()
