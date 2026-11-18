"""
Módulo 3B — Agente Financiero: Mercado Banxico, Inversión, Liquidación y Simulador de Tiempo (market.py)
Define el catálogo de instrumentos gubernamentales de Banxico (CETES, Udibonos, Bondes),
la lógica estricta para invertir, la liquidación de posiciones activas con rendimiento dinámico
según días transcurridos (menos 0.5% de ISR) y el panel "🛠️ Modo Simulador / DevTools"
conectado a `simular_paso_del_tiempo()` de `database.py`.
"""

from typing import Any
import streamlit as st

from database import (
    actualizar_saldo,
    liquidar_inversion,
    obtener_portafolio,
    obtener_saldo,
    registrar_inversion,
    simular_paso_del_tiempo,
)

CATALOGO_BONOS: dict[str, dict[str, Any]] = {
    "CETES 28 Días": {
        "tasa_anual": 11.00,
        "tasa_etiqueta": "11.00% anual",
        "plazo_dias": 28,
        "monto_minimo": 100.0,
        "riesgo": "Muy Bajo (Soberano)",
        "emisor": "Gobierno Federal / Banxico",
        "descripcion": (
            "Certificados de la Tesorería a corto plazo emitidos por el Gobierno Federal."
        ),
    },
    "CETES 91 Días": {
        "tasa_anual": 11.15,
        "tasa_etiqueta": "11.15% anual",
        "plazo_dias": 91,
        "monto_minimo": 100.0,
        "riesgo": "Muy Bajo (Soberano)",
        "emisor": "Gobierno Federal / Banxico",
        "descripcion": (
            "Certificados de la Tesorería a 3 meses con tasa de descuento."
        ),
    },
    "Udibonos 3 Años": {
        "tasa_anual": 9.85,
        "tasa_real_base": 5.35,
        "tasa_etiqueta": "5.35% Real + UDI (~9.85% est.)",
        "plazo_dias": 1095,
        "monto_minimo": 500.0,
        "riesgo": "Bajo (Cobertura Inflacionaria)",
        "emisor": "Gobierno Federal / Banxico",
        "descripcion": (
            "Bonos denominados en UDIs que protegen tu patrimonio contra la inflación."
        ),
    },
    "Bondes F 1 Año": {
        "tasa_anual": 11.30,
        "tasa_etiqueta": "11.30% anual (TIIE Fondeo)",
        "plazo_dias": 364,
        "monto_minimo": 200.0,
        "riesgo": "Bajo (Tasa Variable TIIE)",
        "emisor": "Gobierno Federal / Banxico",
        "descripcion": (
            "Bonos de Desarrollo del Gobierno Federal con tasa revisable referenciada a TIIE de Fondeo."
        ),
    },
}


def calcular_rendimiento_estimado(
    monto: float, tasa_anual: float, plazo_dias: int
) -> tuple[float, float]:
    """
    Calcula el rendimiento bruto estimado al vencimiento y el monto final estimado.
    """
    tasa_decimal = tasa_anual / 100.0 if tasa_anual > 1.0 else tasa_anual
    rendimiento = round(float(monto) * tasa_decimal * (float(plazo_dias) / 365.0), 2)
    monto_final = round(float(monto) + rendimiento, 2)
    return rendimiento, monto_final


def mostrar_market(user_id: int) -> None:
    """
    Renderiza el catálogo de bonos gubernamentales de Banxico (CETES, Udibonos, Bondes),
    el motor de inversión estricta, la tabla/tarjetas de posiciones activas con rendimiento
    dinámico según días transcurridos y el panel plegable "🛠️ Modo Simulador / DevTools".
    """
    st.subheader("🏛️ Mercado de Deuda Gubernamental (Banxico)")
    st.caption(
        "Adquiere y liquida instrumentos soberanos de renta fija respaldados por el Gobierno Federal."
    )

    if "market_mensaje_exito" in st.session_state:
        st.success(st.session_state.pop("market_mensaje_exito"))

    saldo_actual: float = obtener_saldo(user_id)
    st.session_state["saldo_disponible"] = saldo_actual

    st.markdown("### 📊 Catálogo de Instrumentos Disponibles")
    columnas_bonos = st.columns(2)
    nombres_bonos = list(CATALOGO_BONOS.keys())

    for idx, nombre_bono in enumerate(nombres_bonos):
        info = CATALOGO_BONOS[nombre_bono]
        col = columnas_bonos[idx % 2]
        with col:
            with st.container(border=True):
                st.markdown(f"#### 🏦 {nombre_bono}")
                st.caption(info["descripcion"])
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Tasa Anual", f"{info['tasa_anual']:.2f}%")
                with c2:
                    st.metric("Plazo", f"{info['plazo_dias']} días")
                with c3:
                    st.metric("Mínimo", f"${info['monto_minimo']:,.0f}")
                st.markdown(
                    f"**Nivel de Riesgo:** `{info['riesgo']}` | **Detalle Tasa:** {info['tasa_etiqueta']}"
                )

    st.divider()

    st.markdown("### 🛡️ Motor de Inversión Estricta")
    st.info(
        f"💰 **Liquidez Disponible para Invertir:** `${saldo_actual:,.2f} MXN` — "
        "Las órdenes validan tu saldo en tiempo real, descuentan el dinero y registran la operación en el Ledger Inmutable."
    )

    col_selector, col_simulador = st.columns([1.1, 1.0])

    with col_selector:
        tipo_bono = st.selectbox(
            "Selecciona el Instrumento Gubernamental",
            options=nombres_bonos,
            index=0,
        )
        bono_seleccionado = CATALOGO_BONOS[tipo_bono]
        monto_minimo_bono = float(bono_seleccionado["monto_minimo"])

        monto = st.number_input(
            f"Monto a invertir en {tipo_bono} (MXN) — Mínimo ${monto_minimo_bono:,.2f}",
            min_value=10.0,
            value=max(monto_minimo_bono, 100.0),
            step=100.0,
            format="%.2f",
        )

    rendimiento_est, monto_final_est = calcular_rendimiento_estimado(
        monto=float(monto),
        tasa_anual=float(bono_seleccionado["tasa_anual"]),
        plazo_dias=int(bono_seleccionado["plazo_dias"]),
    )

    with col_simulador:
        st.markdown("#### 📈 Proyección de tu Orden al Vencimiento")
        with st.container(border=True):
            m1, m2 = st.columns(2)
            with m1:
                st.metric(
                    label="Rendimiento Estimado al Vencimiento",
                    value=f"+${rendimiento_est:,.2f} MXN",
                    delta=f"{bono_seleccionado['tasa_anual']:.2f}% anual ({bono_seleccionado['plazo_dias']} días)",
                )
            with m2:
                st.metric(
                    label="Monto Final Estimado",
                    value=f"${monto_final_est:,.2f} MXN",
                    delta=f"Capital: ${monto:,.2f} MXN",
                    delta_color="off",
                )

    confirmar_compra = st.button(
        f"✅ Confirmar Compra de {tipo_bono} por ${monto:,.2f} MXN",
        type="primary",
        use_container_width=True,
    )

    if confirmar_compra:
        saldo_actual = obtener_saldo(user_id)
        bono = CATALOGO_BONOS[tipo_bono]
        minimo_requerido = float(bono["monto_minimo"])

        if monto < minimo_requerido:
            st.error(
                f"⚠️ El monto ingresado (${monto:,.2f} MXN) es menor al mínimo requerido "
                f"para **{tipo_bono}** (${minimo_requerido:,.2f} MXN)."
            )
        elif monto > saldo_actual:
            faltante = round(float(monto) - saldo_actual, 2)
            st.error(
                f"❌ **Fondos insuficientes para ejecutar la orden.** "
                f"Intentas invertir **${monto:,.2f} MXN** en **{tipo_bono}**, pero tu saldo "
                f"disponible es de **${saldo_actual:,.2f} MXN** (te faltan **${faltante:,.2f} MXN**). "
                f"Dirígete al módulo de **Wallet** para fondear tu cuenta."
            )
        else:
            exito_saldo, nuevo_saldo, msg_saldo = actualizar_saldo(
                user_id, -float(monto), registrar_movimiento=False
            )
            if not exito_saldo:
                st.error(
                    f"❌ No fue posible descontar el saldo para la inversión: {msg_saldo}"
                )
            else:
                exito_inv, msg_inv = registrar_inversion(
                    user_id, tipo_bono, float(monto)
                )
                if not exito_inv:
                    actualizar_saldo(
                        user_id, float(monto), registrar_movimiento=False
                    )
                    st.error(
                        f"❌ Error al registrar la inversión ({msg_inv}). "
                        "Tu saldo ha sido restaurado íntegramente."
                    )
                else:
                    st.session_state["saldo_disponible"] = nuevo_saldo
                    resumen_compra = (
                        f"🎉 **¡Orden ejecutada con éxito!** Adquiriste **${monto:,.2f} MXN** en "
                        f"**{tipo_bono}** (Tasa {bono['tasa_anual']:.2f}%, Plazo {bono['plazo_dias']} días). "
                        f"Rendimiento estimado al vencimiento: **+${rendimiento_est:,.2f} MXN** "
                        f"(Monto final estimado: **${monto_final_est:,.2f} MXN**). "
                        f"Nuevo saldo disponible: **${nuevo_saldo:,.2f} MXN**."
                    )
                    st.session_state["market_mensaje_exito"] = resumen_compra
                    st.success(resumen_compra)
                    st.rerun()

    st.divider()
    st.markdown("### 📜 Tus Posiciones Activas en Bonos Gubernamentales")

    portafolio_actual = obtener_portafolio(user_id)
    if not portafolio_actual:
        st.caption(
            "Actualmente no tienes posiciones abiertas para liquidar. Adquiere un instrumento arriba para comenzar."
        )
    else:
        st.caption(
            "El **Rendimiento Acumulado** se calcula dinámicamente en tiempo real según los **días transcurridos** "
            r"($\text{Capital} \times \text{Tasa Anual} \times \frac{\text{días transcurridos}}{365}$)."
        )

        # Tabla consolidada de posiciones activas con días transcurridos y ganancia acumulada
        st.dataframe(
            [
                {
                    "Folio": f"#{item['id']}",
                    "Instrumento Banxico": item["tipo_bono"],
                    "Capital Invertido": f"${float(item['monto']):,.2f}",
                    "Tasa Anual": f"{float(item.get('tasa_anual', 11.0)):.2f}%",
                    "Días Transcurridos": f"{int(item.get('dias_transcurridos', 0))} días",
                    "Rendimiento Acumulado": f"+${float(item.get('rendimiento_acumulado', 0.0)):,.2f}",
                    "Fecha de Apertura": item["fecha"],
                }
                for item in portafolio_actual
            ],
            use_container_width=True,
            hide_index=True,
        )

        for item in portafolio_actual:
            inv_id = int(item["id"])
            nombre_bono_pos = str(item["tipo_bono"])
            capital_pos = float(item["monto"])
            fecha_pos = str(item["fecha"])
            dias_trans = int(item.get("dias_transcurridos", 0))
            rend_acumulado = float(item.get("rendimiento_acumulado", 0.0))

            with st.container(border=True):
                c_info, c_capital, c_dias, c_rend, c_accion = st.columns(
                    [2.0, 1.2, 1.1, 1.3, 1.4]
                )
                with c_info:
                    st.markdown(f"**🏦 {nombre_bono_pos}** (`Folio #{inv_id}`)")
                    st.caption(f"Fecha de compra: {fecha_pos}")
                with c_capital:
                    st.metric("Capital", f"${capital_pos:,.2f}")
                with c_dias:
                    st.metric("Días Transcurridos", f"{dias_trans} d")
                with c_rend:
                    st.metric("Rend. Acumulado", f"+${rend_acumulado:,.2f}")
                with c_accion:
                    st.write("")
                    if st.button(
                        "💰 Liquidar / Cobrar",
                        key=f"btn_liquidar_{inv_id}",
                        use_container_width=True,
                    ):
                        exito_liq, mensaje_liq = liquidar_inversion(inv_id, user_id)
                        if exito_liq:
                            st.session_state["saldo_disponible"] = obtener_saldo(
                                user_id
                            )
                            st.session_state["market_mensaje_exito"] = mensaje_liq
                            st.success(mensaje_liq)
                            st.rerun()
                        else:
                            st.error(mensaje_liq)

    st.divider()

    # Sección plegable del Simulador de Tiempo (DevTools)
    with st.expander("🛠️ Modo Simulador / DevTools"):
        st.caption(
            "Adelanta el reloj de tus inversiones activas para simular el envejecimiento del portafolio y observar la generación dinámica de rendimientos."
        )
        col_sim_30, col_sim_365 = st.columns(2)

        with col_sim_30:
            if st.button("Avanzar 30 Días", use_container_width=True):
                exito_sim, msg_sim = simular_paso_del_tiempo(user_id, 30)
                if exito_sim:
                    st.session_state["market_mensaje_exito"] = msg_sim
                    st.rerun()
                else:
                    st.warning(msg_sim)

        with col_sim_365:
            if st.button("Avanzar 1 Año", use_container_width=True):
                exito_sim, msg_sim = simular_paso_del_tiempo(user_id, 365)
                if exito_sim:
                    st.session_state["market_mensaje_exito"] = msg_sim
                    st.rerun()
                else:
                    st.warning(msg_sim)
