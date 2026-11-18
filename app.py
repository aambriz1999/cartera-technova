"""
Módulo 5 — Agente Integrador y Estilos Globales (app.py)
Enrutador principal e identidad visual SaaS de TechNova Bank.
Importa exclusivamente los módulos especializados (`database`, `auth`, `dashboard`,
`wallet`, `market`), aplica el sistema de diseño oscuro y estilos Split-Screen tipo
React/Vue mediante CSS global y dirige el flujo según el estado de sesión en `st.session_state`.
"""

import streamlit as st

from auth import cerrar_sesion, inicializar_estado_sesion, mostrar_auth
from dashboard import mostrar_dashboard
from database import iniciar_db, obtener_saldo
from market import mostrar_market
from wallet import mostrar_wallet


def _inyectar_estilos_globales() -> None:
    """
    Inyecta CSS global para personalizar la identidad visual de TechNova Bank:
      - Fondo principal oscuro elegante (#0E1117).
      - Barra lateral en azul marino corporativo profundo (#07192F -> #0A2540).
      - Estilos Split-Screen SaaS para la columna de marketing (`col_izq` en `auth.py`)
        con tipografía display de gran escala, espaciado elegante, bordes translúcidos y sombras.
      - Botones de formulario (`st.form_submit_button`) al 100% de ancho (full-width)
        con acabado dorado y azul corporativo.
    """
    st.markdown(
        """
        <style>
        /* Fondo principal oscuro elegante y tipografía moderna */
        .stApp {
            background-color: #0E1117;
            background-image: radial-gradient(circle at 12% 18%, rgba(30, 96, 145, 0.14) 0%, transparent 45%),
                              radial-gradient(circle at 88% 82%, rgba(212, 175, 55, 0.08) 0%, transparent 45%);
            color: #F8FAFC;
        }

        /* Barra lateral en Azul Marino Corporativo Profundo */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #07192F 0%, #0A2540 100%) !important;
            border-right: 1px solid rgba(212, 175, 55, 0.32);
        }

        section[data-testid="stSidebar"] * {
            color: #F1F5F9 !important;
        }

        /* ==========================================================================
           ESTILOS SPLIT-SCREEN SAAS FINANCIERO (Columna Izquierda de Marketing)
           ========================================================================== */
        .tn-hero-panel {
            background: linear-gradient(145deg, rgba(13, 27, 46, 0.92) 0%, rgba(10, 21, 38, 0.96) 100%);
            border: 1px solid rgba(212, 175, 55, 0.28);
            border-left: 4px solid #D4AF37;
            border-radius: 20px;
            padding: 2.75rem 2.5rem;
            box-shadow: 0 24px 48px rgba(0, 0, 0, 0.48),
                        inset 0 1px 0 rgba(255, 255, 255, 0.06);
            margin-top: 0.35rem;
        }

        .tn-brand-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(212, 175, 55, 0.12);
            border: 1px solid rgba(212, 175, 55, 0.4);
            color: #E5C158;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            padding: 6px 14px;
            border-radius: 999px;
            margin-bottom: 1.35rem;
        }

        .tn-hero-title {
            font-size: clamp(2.25rem, 3.4vw, 3.1rem) !important;
            font-weight: 800 !important;
            line-height: 1.12 !important;
            letter-spacing: -0.8px !important;
            color: #F8FAFC !important;
            margin: 0 0 1.1rem 0 !important;
        }

        .tn-hero-title span {
            background: linear-gradient(90deg, #D4AF37 0%, #FDE68A 50%, #F59E0B 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .tn-hero-lead {
            color: #CBD5E1;
            font-size: 1.08rem;
            line-height: 1.65;
            margin-bottom: 1.85rem;
            font-weight: 400;
        }

        .tn-feature-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .tn-feature-item {
            display: flex;
            align-items: flex-start;
            gap: 14px;
            background: rgba(22, 32, 50, 0.68);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 14px;
            padding: 1rem 1.15rem;
            transition: all 0.2s ease-in-out;
        }

        .tn-feature-item:hover {
            border-color: rgba(212, 175, 55, 0.45);
            background: rgba(26, 39, 61, 0.85);
            transform: translateX(4px);
        }

        .tn-check-icon {
            flex-shrink: 0;
            width: 28px;
            height: 28px;
            border-radius: 8px;
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            color: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 0.95rem;
            box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3);
            margin-top: 2px;
        }

        .tn-feature-content h4 {
            margin: 0 0 0.22rem 0 !important;
            font-size: 1.02rem !important;
            font-weight: 700 !important;
            color: #F8FAFC !important;
        }

        .tn-feature-content p {
            margin: 0 !important;
            font-size: 0.9rem !important;
            color: #94A3B8 !important;
            line-height: 1.45 !important;
        }

        .tn-trust-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-top: 1.35rem;
            border-top: 1px solid rgba(212, 175, 55, 0.2);
            color: #94A3B8;
            font-size: 0.85rem;
        }

        .tn-trust-stat strong {
            display: block;
            color: #D4AF37;
            font-size: 1.05rem;
            font-weight: 700;
        }

        /* ==========================================================================
           COMPONENTES EJECUTIVOS Y BOTONES FULL-WIDTH
           ========================================================================== */
        div[data-testid="stMetric"] {
            background: linear-gradient(145deg, #151C28 0%, #111722 100%);
            border: 1px solid rgba(212, 175, 55, 0.28);
            border-left: 4px solid #D4AF37;
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
        }

        div[data-testid="stMetricLabel"] p {
            color: #CBD5E1 !important;
            font-weight: 600 !important;
            font-size: 0.96rem !important;
            letter-spacing: 0.3px;
        }

        div[data-testid="stMetricValue"] {
            color: #F8FAFC !important;
            font-weight: 700 !important;
        }

        /* Botones de submit (st.form_submit_button) 100% Full-Width en Dorado / Azul Corporativo */
        div[data-testid="stFormSubmitButton"],
        .stFormSubmitButton {
            width: 100% !important;
        }

        div[data-testid="stFormSubmitButton"] > button,
        .stFormSubmitButton > button {
            width: 100% !important;
            background: linear-gradient(90deg, #D4AF37 0%, #E5C158 50%, #C59B27 100%) !important;
            color: #07192F !important;
            border: 1px solid #F3E5AB !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
            padding: 0.68rem 1.25rem !important;
            transition: all 0.22s ease-in-out !important;
            box-shadow: 0 4px 14px rgba(212, 175, 55, 0.3) !important;
        }

        div[data-testid="stFormSubmitButton"] > button:hover,
        .stFormSubmitButton > button:hover {
            background: linear-gradient(90deg, #1E6091 0%, #0F4C81 100%) !important;
            color: #FFFFFF !important;
            border-color: #D4AF37 !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 18px rgba(30, 96, 145, 0.45) !important;
        }

        /* Botones estándar fuera de formularios */
        .stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #0D9488 0%, #10B981 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(212, 175, 55, 0.45) !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease-in-out !important;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25) !important;
        }

        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(90deg, #10B981 0%, #059669 100%) !important;
            border-color: #D4AF37 !important;
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(212, 175, 55, 0.3) !important;
        }

        .stButton > button[kind="secondary"] {
            background-color: #162032 !important;
            color: #F8FAFC !important;
            border: 1px solid #D4AF37 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease-in-out !important;
        }

        .stButton > button[kind="secondary"]:hover {
            background-color: #1E2D45 !important;
            border-color: #10B981 !important;
            color: #D4AF37 !important;
        }

        /* Contenedores con borde y tarjetas de autenticación */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: rgba(21, 28, 40, 0.84);
            border: 1px solid rgba(212, 175, 55, 0.28) !important;
            border-radius: 18px !important;
            box-shadow: 0 18px 40px rgba(0, 0, 0, 0.38);
        }

        /* Títulos y divisores */
        h1, h2, h3 {
            color: #F8FAFC !important;
            letter-spacing: -0.3px;
        }

        hr {
            border-color: rgba(212, 175, 55, 0.2) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """
    Orquesta la configuración visual global, el inicio de la base de datos
    y el enrutamiento lógico de la aplicación.
    """
    st.set_page_config(
        page_title="TechNova Bank",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _inyectar_estilos_globales()

    # 1. Inicializar tablas de SQLite (banco.db) y estado de sesión
    iniciar_db()
    inicializar_estado_sesion()

    # 2. Enrutamiento: Si no hay sesión activa, mostrar únicamente auth.py
    if (
        not st.session_state.get("authenticated", False)
        or st.session_state.get("user_id") is None
    ):
        mostrar_auth()
        return

    # 3. Enrutamiento: Si hay sesión activa, mostrar menú lateral con Dashboard, Wallet y Market
    user_id: int = int(st.session_state["user_id"])
    username: str = str(st.session_state.get("username", "Inversor"))
    saldo_disponible: float = obtener_saldo(user_id)
    st.session_state["saldo_disponible"] = saldo_disponible

    with st.sidebar:
        st.markdown("## 🏦 TechNova Bank")
        st.caption("Banca Patrimonial & Deuda Soberana")
        st.divider()

        st.markdown(f"**👤 Titular:** `{username}`")
        st.metric(
            label="💧 Liquidez Disponible",
            value=f"${saldo_disponible:,.2f} MXN",
        )
        st.divider()

        vista_activa = st.radio(
            "Menú Principal",
            options=["Dashboard", "Wallet", "Market"],
            index=0,
        )

        st.divider()
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            cerrar_sesion()

    st.markdown(
        """
        <div style="display: flex; align-items: center; justify-content: space-between;
                    padding: 0.25rem 0 0.75rem 0; border-bottom: 1px solid rgba(212, 175, 55, 0.25); margin-bottom: 1.25rem;">
            <div>
                <h1 style="margin: 0; font-size: 2rem;">🏦 TechNova Bank <span style="color: #D4AF37; font-weight: 400;">| Private Wealth</span></h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if vista_activa == "Dashboard":
        mostrar_dashboard(user_id)
    elif vista_activa == "Wallet":
        mostrar_wallet(user_id)
    elif vista_activa == "Market":
        mostrar_market(user_id)


if __name__ == "__main__":
    main()
