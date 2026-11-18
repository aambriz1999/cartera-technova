"""
Módulo 2 — Capa de Interfaz y Seguridad de Autenticación (auth.py)
Diseño de Tarjeta Central encapsulada con `col1, col2, col3 = st.columns([1, 1.5, 1])`,
título centrado "🏦 TechNova Bank" con subtítulo sutil, pestañas `🔑 Iniciar Sesión` y
`📝 Crear Cuenta`, botones con `use_container_width=True` y validaciones de Regex (`re`)
y longitud mínima de contraseña (8 caracteres).
"""

import re
import streamlit as st

from database import registrar_usuario, validar_login

MIN_PASSWORD_LENGTH: int = 8
EMAIL_REGEX: str = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


def es_correo_valido(correo: str) -> bool:
    """
    Valida mediante expresiones regulares (`re.match`) que la cadena ingresada
    tenga el formato estándar de un correo electrónico válido.
    """
    if not correo:
        return False
    return re.match(EMAIL_REGEX, correo.strip()) is not None


def inicializar_estado_sesion() -> None:
    """
    Inicializa las claves requeridas en `st.session_state` si aún no existen:
      - `authenticated` (bool)
      - `user_id` (int | None)
      - `username` (str | None)
      - `saldo_disponible` (float)
    """
    valores_por_defecto = {
        "authenticated": False,
        "user_id": None,
        "username": None,
        "saldo_disponible": 0.0,
    }
    for clave, valor_defecto in valores_por_defecto.items():
        if clave not in st.session_state:
            st.session_state[clave] = valor_defecto


def cerrar_sesion() -> None:
    """
    Limpia el estado de sesión del usuario en `st.session_state` y recarga la vista.
    """
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["username"] = None
    st.session_state["saldo_disponible"] = 0.0
    st.rerun()


def mostrar_auth() -> None:
    """
    Renderiza la pantalla de autenticación en una Tarjeta Central encapsulada
    con `col1, col2, col3 = st.columns([1, 1.5, 1])`.
    """
    inicializar_estado_sesion()

    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        with st.container(border=True):
            st.markdown(
                """
                <div style="text-align: center; padding: 0.75rem 0.5rem 0.5rem 0.5rem;">
                    <h1 style="margin-bottom: 0.25rem;">🏦 TechNova Bank</h1>
                    <p style="color: #94A3B8; font-size: 0.98rem; margin-top: 0;">
                        Banca Patrimonial & Cartera de Inversión Soberana
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.divider()

            tab_login, tab_registro = st.tabs(
                ["🔑 Iniciar Sesión", "📝 Crear Cuenta"]
            )

            with tab_login:
                with st.form("form_login", clear_on_submit=False):
                    username_login = st.text_input(
                        "Correo electrónico",
                        placeholder="ejemplo@technova.com",
                        key="login_username_input",
                    )
                    password_login = st.text_input(
                        "Contraseña",
                        type="password",
                        placeholder="Ingresa tu contraseña",
                        key="login_password_input",
                    )
                    submit_login = st.form_submit_button(
                        "🔑 Iniciar Sesión",
                        use_container_width=True,
                        type="primary",
                    )

                if submit_login:
                    correo_login = (username_login or "").strip()
                    if not correo_login or not password_login:
                        st.error(
                            "Por favor, ingresa tu correo electrónico y contraseña."
                        )
                    else:
                        user_data = validar_login(correo_login, password_login)
                        if user_data is not None:
                            st.session_state["authenticated"] = True
                            st.session_state["user_id"] = int(user_data["id"])
                            st.session_state["username"] = str(
                                user_data["username"]
                            )
                            st.session_state["saldo_disponible"] = float(
                                user_data["saldo_disponible"]
                            )
                            st.success(
                                f"¡Bienvenido de nuevo, {user_data['username']}!"
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Credenciales inválidas. Verifica tu correo electrónico y contraseña."
                            )

            with tab_registro:
                st.caption(
                    "🔒 Requisitos: correo electrónico válido y contraseña de mínimo 8 caracteres."
                )
                with st.form("form_registro", clear_on_submit=False):
                    email_reg = st.text_input(
                        "Correo electrónico",
                        placeholder="cliente@correo.com",
                        key="reg_username_input",
                    )
                    password_reg = st.text_input(
                        "Contraseña",
                        type="password",
                        placeholder=f"Mínimo {MIN_PASSWORD_LENGTH} caracteres",
                        key="reg_password_input",
                    )
                    confirm_password_reg = st.text_input(
                        "Confirmar contraseña",
                        type="password",
                        placeholder="Repite tu contraseña",
                        key="reg_confirm_password_input",
                    )
                    submit_registro = st.form_submit_button(
                        "📝 Crear Cuenta",
                        use_container_width=True,
                        type="primary",
                    )

                if submit_registro:
                    correo_limpio = (email_reg or "").strip()

                    if not es_correo_valido(correo_limpio):
                        st.error(
                            "❌ Formato de correo inválido. Debes ingresar una dirección de correo electrónico válida (ej. usuario@dominio.com)."
                        )
                    elif (
                        not password_reg
                        or len(password_reg) < MIN_PASSWORD_LENGTH
                    ):
                        st.error(
                            f"❌ Contraseña insegura: debe contener al menos {MIN_PASSWORD_LENGTH} caracteres."
                        )
                    elif password_reg != confirm_password_reg:
                        st.error("❌ Las contraseñas ingresadas no coinciden.")
                    else:
                        exito, mensaje = registrar_usuario(
                            correo_limpio, password_reg
                        )
                        if exito:
                            st.success(
                                f"✅ {mensaje} Ahora puedes ingresar desde la pestaña '🔑 Iniciar Sesión'."
                            )
                        else:
                            st.error(f"❌ {mensaje}")
