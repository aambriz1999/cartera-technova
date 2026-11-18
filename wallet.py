"""
Módulo 3A — Agente Financiero: Billetera, Liquidez y Estado de Cuenta (wallet.py)
Construye la interfaz para fondear (depositar) y retirar dinero de la cuenta,
y muestra el Estado de Cuenta (Ledger Inmutable) conectándose exclusivamente
a las funciones aisladas de `database.py`.
"""

import streamlit as st

from database import (
    actualizar_saldo,
    obtener_historial,
    obtener_portafolio,
    obtener_saldo,
)


def mostrar_wallet(user_id: int) -> None:
    """
    Renderiza la interfaz de la billetera digital (Wallet) del usuario.
    Sincroniza el saldo disponible con `database.py`, permite realizar
    depósitos (fondeo) y retiros de efectivo con validación estricta, y
    despliega al final la tabla con el Estado de Cuenta (`obtener_historial`).
    """
    st.subheader("💳 Billetera Digital y Gestión de Liquidez")
    st.caption(
        "Administra tu efectivo disponible en MXN para operar instrumentos gubernamentales de Banxico."
    )

    if "wallet_mensaje_exito" in st.session_state:
        st.success(st.session_state.pop("wallet_mensaje_exito"))

    # Consultar saldo real desde database.py y sincronizar st.session_state
    saldo_actual: float = obtener_saldo(user_id)
    st.session_state["saldo_disponible"] = saldo_actual

    portafolio = obtener_portafolio(user_id)
    capital_invertido: float = round(
        sum(float(inv.get("monto", 0.0)) for inv in portafolio), 2
    )
    patrimonio_total: float = round(saldo_actual + capital_invertido, 2)

    col_saldo, col_invertido, col_patrimonio = st.columns(3)
    with col_saldo:
        st.metric(
            label="Saldo Disponible en Cuenta (MXN)",
            value=f"${saldo_actual:,.2f} MXN",
            delta="Liquidez inmediata",
        )
    with col_invertido:
        st.metric(
            label="Capital Invertido en Bonos (MXN)",
            value=f"${capital_invertido:,.2f} MXN",
            delta=f"{len(portafolio)} operaciones activas",
            delta_color="off",
        )
    with col_patrimonio:
        st.metric(
            label="Patrimonio Total en Cuenta (MXN)",
            value=f"${patrimonio_total:,.2f} MXN",
        )

    st.divider()

    col_fondear, col_retirar = st.columns(2)

    with col_fondear:
        st.markdown("### 💵 Fondear Cuenta (Depósito)")
        st.write(
            "Ingresa recursos a tu cuenta concentradora TechNova para adquirir instrumentos de deuda."
        )
        with st.form("form_fondear", clear_on_submit=False):
            origen_fondos = st.selectbox(
                "Método de fondeo",
                options=[
                    "Transferencia SPEI (CLABE Interbancaria)",
                    "Tarjeta de Débito Bancaria",
                    "Domiciliación Cuenta Eje",
                ],
            )
            monto_deposito = st.number_input(
                "Monto a depositar (MXN)",
                min_value=10.0,
                value=1000.0,
                step=100.0,
                format="%.2f",
            )
            btn_fondear = st.form_submit_button(
                "📥 Confirmar Depósito",
                use_container_width=True,
                type="primary",
            )

            if btn_fondear:
                if monto_deposito <= 0:
                    st.error("El monto a depositar debe ser mayor a $0.00 MXN.")
                else:
                    exito, nuevo_saldo, mensaje = actualizar_saldo(
                        user_id, float(monto_deposito)
                    )
                    if exito:
                        st.session_state["saldo_disponible"] = nuevo_saldo
                        msg_ok = (
                            f"✅ Depósito de ${monto_deposito:,.2f} MXN vía {origen_fondos} "
                            f"aplicado con éxito. Nuevo saldo disponible: ${nuevo_saldo:,.2f} MXN."
                        )
                        st.session_state["wallet_mensaje_exito"] = msg_ok
                        st.success(msg_ok)
                        st.rerun()
                    else:
                        st.error(f"❌ No fue posible procesar el depósito: {mensaje}")

    with col_retirar:
        st.markdown("### 🏧 Retirar Fondos")
        st.write(
            "Transfiere tu liquidez disponible hacia tu cuenta bancaria registrada sin comisiones."
        )
        with st.form("form_retirar", clear_on_submit=False):
            destino_fondos = st.selectbox(
                "Cuenta destino del retiro",
                options=[
                    "Cuenta CLABE Bancaria Principal (SPEI)",
                    "Tarjeta de Débito Vinculada",
                ],
            )
            monto_retiro = st.number_input(
                "Monto a retirar (MXN)",
                min_value=10.0,
                value=100.0,
                step=100.0,
                format="%.2f",
            )
            btn_retirar = st.form_submit_button(
                "📤 Confirmar Retiro",
                use_container_width=True,
            )

            if btn_retirar:
                saldo_verificado = obtener_saldo(user_id)
                if monto_retiro <= 0:
                    st.error("El monto a retirar debe ser mayor a $0.00 MXN.")
                elif monto_retiro > saldo_verificado:
                    st.error(
                        f"❌ Fondos insuficientes para realizar el retiro. "
                        f"Solicitaste ${monto_retiro:,.2f} MXN, pero tu saldo disponible es de "
                        f"${saldo_verificado:,.2f} MXN."
                    )
                else:
                    exito, nuevo_saldo, mensaje = actualizar_saldo(
                        user_id, -float(monto_retiro)
                    )
                    if exito:
                        st.session_state["saldo_disponible"] = nuevo_saldo
                        msg_ok = (
                            f"✅ Retiro de ${monto_retiro:,.2f} MXN hacia {destino_fondos} "
                            f"procesado exitosamente. Nuevo saldo disponible: ${nuevo_saldo:,.2f} MXN."
                        )
                        st.session_state["wallet_mensaje_exito"] = msg_ok
                        st.success(msg_ok)
                        st.rerun()
                    else:
                        st.error(f"❌ Error al procesar el retiro: {mensaje}")

    st.divider()

    # Sección de Estado de Cuenta (Ledger Inmutable)
    st.markdown("### 📑 Estado de Cuenta — Historial de Movimientos")
    st.caption(
        "Registro inmutable de todas tus operaciones de Fondeo, Retiro, Compra de Bonos y Liquidaciones."
    )

    historial = obtener_historial(user_id)
    if historial:
        st.dataframe(
            [
                {
                    "ID Movimiento": f"#{mov['id']}",
                    "Tipo de Operación": mov["tipo_operacion"],
                    "Monto (MXN)": f"${float(mov['monto']):,.2f}",
                    "Fecha y Hora": mov["fecha"],
                }
                for mov in historial
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "Aún no se registran movimientos en tu estado de cuenta. Realiza un depósito para comenzar."
        )
