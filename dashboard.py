"""
Módulo 4 — Agente de UI/UX: Visualización Ejecutiva (dashboard.py)
Construye el panel de control panorámico usando Plotly Express (`template='plotly_dark'`)
y Streamlit. Muestra las tarjetas ejecutivas de métricas (🏛️ Patrimonio, 💧 Liquidez,
📊 Portafolio), una gráfica de pastel interactiva con fondo transparente en paleta
azul y dorado, y el desglose del portafolio organizado en columnas (`st.columns`).
"""

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from database import obtener_portafolio, obtener_saldo

# Paleta corporativa TechNova Bank (Tonos Azules Profundos, Dorados y Esmeralda)
PALETA_CORPORATIVA: list[str] = [
    "#D4AF37",  # Dorado Institucional TechNova
    "#1E6091",  # Azul Marino Real
    "#2E86AB",  # Azul Cobalto Financiero
    "#F59E0B",  # Ámbar Dorado
    "#10B981",  # Verde Esmeralda
    "#0F4C81",  # Azul Profundo
    "#64748B",  # Gris Pizarra Ejecutivo (Liquidez)
]


def _agrupar_por_instrumento(
    portafolio: list[dict[str, Any]], total_invertido: float
) -> list[dict[str, Any]]:
    """
    Agrupa las posiciones del portafolio por `tipo_bono`, calculando el monto
    acumulado, rendimiento acumulado, número de operaciones y porcentaje de participación.
    """
    acumulado: dict[str, dict[str, Any]] = {}

    for item in portafolio:
        bono = str(item.get("tipo_bono", "Instrumento"))
        monto = round(float(item.get("monto", 0.0)), 2)
        rendimiento = round(float(item.get("rendimiento_acumulado", 0.0)), 2)

        if bono not in acumulado:
            acumulado[bono] = {
                "tipo_bono": bono,
                "monto": 0.0,
                "rendimiento_acumulado": 0.0,
                "operaciones": 0,
            }
        acumulado[bono]["monto"] = round(acumulado[bono]["monto"] + monto, 2)
        acumulado[bono]["rendimiento_acumulado"] = round(
            acumulado[bono]["rendimiento_acumulado"] + rendimiento, 2
        )
        acumulado[bono]["operaciones"] += 1

    resumen: list[dict[str, Any]] = []
    for datos in acumulado.values():
        monto_bono = datos["monto"]
        participacion = (
            round((monto_bono / total_invertido) * 100, 2)
            if total_invertido > 0
            else 0.0
        )
        resumen.append(
            {
                "tipo_bono": datos["tipo_bono"],
                "monto": monto_bono,
                "rendimiento_acumulado": datos["rendimiento_acumulado"],
                "operaciones": datos["operaciones"],
                "participacion_pct": participacion,
            }
        )

    resumen.sort(key=lambda x: x["monto"], reverse=True)
    return resumen


def _crear_grafica_pastel(
    datos_grafica: list[dict[str, Any]],
    titulo: str,
    etiqueta_centro: str,
    monto_centro: float,
) -> Any:
    """
    Construye una gráfica de pastel interactiva (`px.pie`) con tema oscuro
    (`template='plotly_dark'`), paleta corporativa azul/dorado y fondo transparente.
    """
    df_chart = pd.DataFrame(datos_grafica)

    fig = px.pie(
        df_chart,
        names="tipo_bono",
        values="monto",
        hole=0.48,
        title=titulo,
        template="plotly_dark",
        color_discrete_sequence=PALETA_CORPORATIVA,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        insidetextfont=dict(color="#F8FAFC", size=12),
        hovertemplate=(
            "<b>🏦 %{label}</b><br>"
            "Capital Asignado: <b>$%{value:,.2f} MXN</b><br>"
            "Peso en Cartera: <b>%{percent}</b><extra></extra>"
        ),
        marker=dict(line=dict(color="#0E1117", width=2.5)),
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title_font=dict(size=17, color="#F8FAFC"),
        margin=dict(t=55, b=30, l=15, r=15),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.22,
            xanchor="center",
            x=0.5,
            font=dict(color="#E2E8F0", size=12),
            title=None,
        ),
        annotations=[
            dict(
                text=(
                    f"<span style='color:#D4AF37;font-size:12px'>{etiqueta_centro}</span>"
                    f"<br><b style='color:#F8FAFC;font-size:15px'>${monto_centro:,.2f}</b>"
                ),
                x=0.5,
                y=0.5,
                showarrow=False,
            )
        ],
    )

    return fig


def mostrar_dashboard(user_id: int) -> None:
    """
    Renderiza el Panel Ejecutivo Widescreen de TechNova Bank:
      - Fila superior en 3 columnas con `st.metric` (🏛️ Patrimonio, 💧 Liquidez, 📊 Portafolio).
      - Cuerpo panorámico organizado en columnas (`st.columns`) con la gráfica interactiva
        `px.pie` (`template='plotly_dark'`) a la izquierda y las tablas analíticas a la derecha.
    """
    liquidez: float = round(float(obtener_saldo(user_id)), 2)
    st.session_state["saldo_disponible"] = liquidez

    portafolio: list[dict[str, Any]] = obtener_portafolio(user_id)
    total_invertido: float = round(
        sum(float(item["monto"]) for item in portafolio), 2
    )
    rendimiento_acumulado_total: float = round(
        sum(float(item.get("rendimiento_acumulado", 0.0)) for item in portafolio),
        2,
    )
    patrimonio_total: float = round(liquidez + total_invertido, 2)

    st.subheader("📊 Panel Ejecutivo de Gestión Patrimonial")
    st.caption(
        "Monitoreo en tiempo real de tu distribución de activos soberanos, liquidez y rendimiento acumulado."
    )

    if patrimonio_total > 0:
        pct_invertido = round((total_invertido / patrimonio_total) * 100, 1)
        pct_liquidez = round((liquidez / patrimonio_total) * 100, 1)
        delta_patrimonio = f"{pct_invertido:.1f}% en renta fija"
        delta_liquidez = f"{pct_liquidez:.1f}% disponible en efectivo"
    else:
        delta_patrimonio = "Cuenta sin fondear"
        delta_liquidez = "0.0% del patrimonio"

    num_posiciones = len(portafolio)
    if rendimiento_acumulado_total > 0:
        delta_portafolio = (
            f"{num_posiciones} pos. | +${rendimiento_acumulado_total:,.2f} MXN acum."
        )
    else:
        delta_portafolio = (
            f"{num_posiciones} "
            f"{'posición activa' if num_posiciones == 1 else 'posiciones activas'}"
        )

    # 1. Fila Superior: 3 Tarjetas de Métricas Ejecutivas (KPIs)
    col_patrimonio, col_liquidez, col_portafolio = st.columns(3, gap="medium")

    with col_patrimonio:
        st.metric(
            label="🏛️ Patrimonio",
            value=f"${patrimonio_total:,.2f} MXN",
            delta=delta_patrimonio,
            delta_color="normal" if total_invertido > 0 else "off",
            help="Suma consolidada de tu Liquidez más el capital activo en Portafolio.",
        )

    with col_liquidez:
        st.metric(
            label="💧 Liquidez",
            value=f"${liquidez:,.2f} MXN",
            delta=delta_liquidez,
            delta_color="off",
            help="Efectivo líquido disponible en tu Wallet para invertir o retirar.",
        )

    with col_portafolio:
        st.metric(
            label="📊 Portafolio",
            value=f"${total_invertido:,.2f} MXN",
            delta=delta_portafolio,
            delta_color="normal" if num_posiciones > 0 else "off",
            help="Capital colocado en instrumentos gubernamentales de Banxico.",
        )

    st.divider()

    # 2. Cuerpo Principal Panorámico en Columnas (Widescreen Control Panel)
    if len(portafolio) > 0:
        resumen_instrumentos = _agrupar_por_instrumento(
            portafolio, total_invertido
        )

        col_visual, col_analitica = st.columns([1.05, 1.35], gap="large")

        with col_visual:
            with st.container(border=True):
                incluir_liquidez = st.toggle(
                    "Incluir 💧 Liquidez en la gráfica de distribución",
                    value=False,
                )

                datos_grafica = [
                    {"tipo_bono": item["tipo_bono"], "monto": item["monto"]}
                    for item in resumen_instrumentos
                ]

                if incluir_liquidez and liquidez > 0:
                    datos_grafica.append(
                        {
                            "tipo_bono": "Liquidez Disponible",
                            "monto": liquidez,
                        }
                    )
                    titulo_grafica = "Composición Global del Patrimonio"
                    etiqueta_centro = "PATRIMONIO"
                    monto_centro = patrimonio_total
                else:
                    titulo_grafica = "Asignación de Activos por Instrumento"
                    etiqueta_centro = "PORTAFOLIO"
                    monto_centro = total_invertido

                fig = _crear_grafica_pastel(
                    datos_grafica=datos_grafica,
                    titulo=titulo_grafica,
                    etiqueta_centro=etiqueta_centro,
                    monto_centro=monto_centro,
                )
                st.plotly_chart(fig, use_container_width=True)

                instrumento_lider = resumen_instrumentos[0]
                st.caption(
                    f"🏆 **Activo Principal:** `{instrumento_lider['tipo_bono']}` concentra el "
                    f"**{instrumento_lider['participacion_pct']:.2f}%** del portafolio "
                    f"(${instrumento_lider['monto']:,.2f} MXN)."
                )

        with col_analitica:
            with st.container(border=True):
                st.markdown("#### 📌 Concentración por Instrumento Banxico")
                df_resumen = pd.DataFrame(resumen_instrumentos)
                st.dataframe(
                    df_resumen,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "tipo_bono": st.column_config.TextColumn(
                            "Instrumento"
                        ),
                        "operaciones": st.column_config.NumberColumn(
                            "Órdenes",
                            format="%d",
                        ),
                        "monto": st.column_config.NumberColumn(
                            "Capital (MXN)",
                            format="$%.2f",
                        ),
                        "rendimiento_acumulado": st.column_config.NumberColumn(
                            "Rend. Acumulado",
                            format="+$%.2f",
                        ),
                        "participacion_pct": st.column_config.ProgressColumn(
                            "% Peso",
                            format="%.2f%%",
                            min_value=0.0,
                            max_value=100.0,
                        ),
                    },
                )

            with st.container(border=True):
                st.markdown("#### 🗂️ Desglose de Posiciones Activas")
                df_historial = pd.DataFrame(
                    [
                        {
                            "Folio": f"#{int(item['id'])}",
                            "Instrumento": str(item["tipo_bono"]),
                            "Capital (MXN)": f"${float(item['monto']):,.2f}",
                            "Días": f"{int(item.get('dias_transcurridos', 0))} d",
                            "Ganancia Acum.": f"+${float(item.get('rendimiento_acumulado', 0.0)):,.2f}",
                            "Apertura": str(item["fecha"]),
                        }
                        for item in portafolio
                    ]
                )
                st.dataframe(
                    df_historial,
                    use_container_width=True,
                    hide_index=True,
                )

    else:
        col_empty_izq, col_empty_der = st.columns([1.05, 1.35], gap="large")

        with col_empty_izq:
            with st.container(border=True):
                if liquidez > 0:
                    fig_liquidez = _crear_grafica_pastel(
                        datos_grafica=[
                            {
                                "tipo_bono": "Liquidez Disponible",
                                "monto": liquidez,
                            }
                        ],
                        titulo="Distribución Patrimonial (100% Liquidez)",
                        etiqueta_centro="LIQUIDEZ",
                        monto_centro=liquidez,
                    )
                    st.plotly_chart(fig_liquidez, use_container_width=True)
                else:
                    st.info(
                        "💡 **Tu portafolio aún no registra activos.**\n\n"
                        "Fondea tu cuenta en **Wallet** para activar la visualización gráfica."
                    )

        with col_empty_der:
            with st.container(border=True):
                st.markdown("#### 🧭 Guía Ejecutiva de Inversión — TechNova Bank")
                st.write(
                    "Comienza a construir tu portafolio de renta fija soberana en 3 pasos:"
                )
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(
                        "**1. 💧 Fondea**\n\n"
                        "Ingresa al módulo **Wallet** y realiza un depósito vía SPEI o tarjeta."
                    )
                with c2:
                    st.markdown(
                        "**2. 🏛️ Invierte**\n\n"
                        "En **Market**, adquiere **CETES**, **Udibonos** o **Bondes F**."
                    )
                with c3:
                    st.markdown(
                        "**3. 📊 Monitorea**\n\n"
                        "Visualiza tu rendimiento dinámico y cobra tus posiciones al vencimiento."
                    )
