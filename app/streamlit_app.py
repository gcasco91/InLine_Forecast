import streamlit as st
import pandas as pd
import os
import sys
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


# Para importar desde raíz del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.forecast.forecast_module import forecast_idioma
from src.forecast.forecast_futuro import forecast_futuro
from app.home import home
from src.workforce.erlang_calculator import estimar_fte_erlang_c


st.set_page_config(page_title="InLine", layout="wide")
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# --- Función para múltiples idiomas ---
def forecast_multiidioma(df, idiomas, clientes):
    df_total = []
    metricas_total = {}
    modelos_total = {}

    for idioma in idiomas:
        df_i, modelo_i, metricas_i = forecast_idioma(df, idioma, clientes)
        if df_i is not None:
            df_i["idioma"] = idioma
            df_total.append(df_i)
            metricas_total[idioma] = metricas_i
            modelos_total[idioma] = modelo_i

    if df_total:
        df_preparados = []
        for df in df_total:
            # Si el índice es "date" y además ya hay una columna "date", eliminamos la columna para evitar conflicto
            if "date" in df.index.names and "date" in df.columns:
                df = df.drop(columns="date").reset_index()
            elif "date" in df.index.names:
                df = df.reset_index()
            df_preparados.append(df)

        df_forecast_all = pd.concat(df_preparados, ignore_index=True).sort_values("date")


        return df_forecast_all, modelos_total, metricas_total
    else:
        return None, None, None

# --- Forecast futuro por idioma ---
def forecast_futuro_multiidioma(modelos_dict, df_forecast_all, n_dias):
    from src.forecast.forecast_futuro import forecast_futuro

    df_futuro_total = []

    for idioma, modelo in modelos_dict.items():
        df_hist = df_forecast_all[df_forecast_all["idioma"] == idioma].copy()
        df_hist.set_index("date", inplace=True)
        df_hist["y"] = df_hist["real"]

        df_fut = forecast_futuro(modelo, df_hist, n_dias=n_dias)
        if df_fut is not None:
            df_fut["idioma"] = idioma

            # Extraer cliente desde df_hist (único por idioma)
            cliente = df_hist["cliente"].iloc[0] if "cliente" in df_hist.columns else "desconocido"
            df_fut["cliente"] = cliente

            df_futuro_total.append(df_fut)

    if df_futuro_total:
        df_futuro_all = pd.concat(df_futuro_total).sort_values(["idioma", "date"])
        return df_futuro_all
    else:
        return None

# --- Interfaz principal ---

st.sidebar.title("⚙️InLine - Menu")
seccion = st.sidebar.radio("Ir a:", ["🗃️Carga de datos", "🌍Forecast por idioma", "👥Estimación de FTEs (Erlang C)"])


if seccion == "🗃️Carga de datos":
    df = home()

elif seccion == "🌍Forecast por idioma":
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path_datos = os.path.join(root_path, "data", "processed", "llamadas_diarias.csv")

    if not os.path.exists(path_datos):
        st.warning("⚠️ No se encontró el archivo procesado.")
    else:
        df = pd.read_csv(path_datos, parse_dates=["date"])

        clientes = df["cliente"].unique().tolist()
        idiomas = df["idioma"].unique().tolist()

        cliente_sel = st.multiselect("Selecciona cliente(s)", clientes, default=clientes)
        idioma_sel = st.multiselect("Selecciona idioma(s)", idiomas, default=idiomas)

        st.subheader("⏩ Forecast a futuro")
        col1, col2 = st.columns(2)
        with col1:
            cantidad = st.selectbox("Cantidad", list(range(1, 13)), index=1)
        with col2:
            unidad = st.selectbox("Unidad de tiempo", ["semanas", "meses"])

        n_dias = cantidad * (5 if unidad == "semanas" else 20)

        st.markdown("""
            <div style="font-size: 0.85rem; line-height: 1.5;">
            <b>ℹ️ ¿Qué significan las métricas?</b><br><br>
            • <b>MAE</b> (Mean Absolute Error): mide el error promedio en unidades absolutas. Cuanto menor, mejor.<br>
            • <b>RMSE</b> (Root Mean Squared Error): penaliza más los errores grandes. Es útil si te importa evitar desviaciones importantes.<br>
            • <b>MAPE</b> (Mean Absolute Percentage Error): expresa el error en porcentaje respecto al valor real. Puede ser engañoso si hay días con pocas llamadas.
            </div>
            """, unsafe_allow_html=True)

        if st.button("Generar Forecast"):

            df_forecast, modelos_dict, metricas = forecast_multiidioma(df, idioma_sel, cliente_sel)

            if df_forecast is not None:
                # Forecast futuro
                df_future = forecast_futuro_multiidioma(modelos_dict, df_forecast, n_dias=n_dias)

                # Agregar columna AHT por idioma desde histórico
                if "aht" in df_forecast.columns:
                    df_aht = df_forecast.groupby("idioma")["aht"].mean().reset_index()
                    df_future = df_future.merge(df_aht, on="idioma", how="left")

                if "aht_x" in df_future.columns and "aht_y" in df_future.columns:
                    df_future["aht"] = df_future["aht_y"]
                    df_future.drop(columns=["aht_x", "aht_y"], inplace=True)

                # Guardar forecast futuro en /data/processed
                df_future.to_csv(os.path.join(root_path, "data", "processed", "forecast_futuro.csv"), index=False)

                # Forecast combinado
                df_hist_plot = df_forecast[["date", "real", "pred", "ic_95_inf", "ic_95_sup", "idioma"]].copy()
                df_hist_plot["tipo"] = "Histórico"

                df_future_plot = df_future.copy()
                df_future_plot["real"] = np.nan
                df_future_plot["tipo"] = "Futuro"

                df_combinado = pd.concat([df_hist_plot, df_future_plot], ignore_index=True)
                df_combinado.sort_values(["idioma", "date"], inplace=True)

                # 👇 Asegurar que 'date' sea índice
                if "date" in df_combinado.columns:
                    df_combinado = df_combinado.set_index("date")
                elif "date" in df_combinado.index.names:
                    df_combinado = df_combinado.reset_index().set_index("date")

                # --- TABS ---
                tabs = st.tabs(["📊 Forecast & Métricas", "📈 Tabla Forecast"])

                with tabs[0]:
                    st.subheader("📊 Métricas de evaluación por idioma")

                    # Transformar el dict a DataFrame y formatear
                    df_metricas = pd.DataFrame(metricas).T.reset_index()
                    df_metricas.rename(columns={"index": "Idioma"}, inplace=True)
                    df_metricas = df_metricas[["Idioma", "MAE", "RMSE", "MAPE"]].round(1)
                    df_metricas = df_metricas.round(2).sort_values("MAPE")

                    st.dataframe(df_metricas, use_container_width=True)


                    st.subheader("📈 Forecast combinado (Histórico + Futuro)")
                    
                    for idioma in idioma_sel:
                        st.markdown(f"### 📌 Idioma: {idioma}")

                        df_idioma = df_combinado[df_combinado["idioma"] == idioma].copy()
                        df_idioma = df_idioma.reset_index()  # Asegura columna 'date'

                        fig = go.Figure()

                        # Línea de predicción
                        fig.add_trace(go.Scatter(
                            x=df_idioma["date"], y=df_idioma["pred"],
                            mode="lines", name="Predicción", line=dict(color="royalblue")
                        ))

                        # Línea real
                        fig.add_trace(go.Scatter(
                            x=df_idioma["date"], y=df_idioma["real"],
                            mode="lines", name="Real", line=dict(color="black")
                        ))

                        # Área del intervalo de confianza
                        fig.add_trace(go.Scatter(
                            x=pd.concat([df_idioma["date"], df_idioma["date"][::-1]]),
                            y=pd.concat([df_idioma["ic_95_sup"], df_idioma["ic_95_inf"][::-1]]),
                            fill='toself',
                            fillcolor='rgba(135, 206, 250, 0.2)',  # celeste semitransparente
                            line=dict(color='rgba(255,255,255,0)'),
                            name="IC 95%"
                        ))

                        fig.update_layout(
                            xaxis_title="Fecha",
                            yaxis_title="Llamadas",
                            hovermode="x unified",
                            margin=dict(l=30, r=30, t=40, b=30),
                            height=400
                        )

                        st.plotly_chart(fig, use_container_width=True)


                with tabs[1]:
                    st.subheader(f"🔮 Forecast futuro ({cantidad} {unidad} ≈ {n_dias} días hábiles)")
                    df_tabla = df_future.copy()
                    df_tabla[["pred", "ic_95_inf", "ic_95_sup"]] = df_tabla[["pred", "ic_95_inf", "ic_95_sup"]].round(0).astype(int)
                    st.dataframe(df_tabla)

                    csv_fut = df_tabla.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Descargar forecast futuro en CSV",
                        data=csv_fut,
                        file_name=f"forecast_futuro_multi_{'_'.join(cliente_sel)}.csv",
                        mime="text/csv"
                    )

          
            else:
                st.error("❌ No se pudo generar el forecast (datos insuficientes).")


elif seccion == "👥Estimación de FTEs (Erlang C)":

    st.subheader("👥 Estimación de FTEs para todos los idiomas")

    path_futuro = os.path.join(root_path, "data", "processed", "forecast_futuro.csv")

    if not os.path.exists(path_futuro):
        st.warning("⚠️ Primero generá el forecast futuro desde la pestaña 'Forecast por idioma'.")
    else:
        df_future = pd.read_csv(path_futuro, parse_dates=["date"])

        # Limpieza de columnas duplicadas
        if "aht_x" in df_future.columns and "aht_y" in df_future.columns:
            df_future["aht"] = df_future["aht_y"]
            df_future.drop(columns=["aht_x", "aht_y"], inplace=True)

        if "aht" not in df_future.columns:
            st.error("⚠️ El archivo no contiene la columna 'aht'.")
        elif df_future["aht"].dropna().empty:
            st.warning("⚠️ La columna 'aht' está vacía.")
        else:
            idiomas = df_future["idioma"].unique().tolist()

            tabs = st.tabs(["🔧 Parámetros", "📈 Resultados"])

            with tabs[0]:
                st.markdown("Ajustá los parámetros del modelo Erlang C:")

                col1, col2, col3 = st.columns(3)
                with col1:
                    asa = st.number_input("ASA objetivo (segundos)", value=30)
                with col2:
                    sla = st.slider("SLA objetivo (%)", 30, 100, 70)
                with col3:
                    shrinkage = st.slider("Shrinkage (%)", 0, 70, 30)

                st.markdown("#### ⚙️ Selección de AHT")

                modo_aht = st.radio(
                    "¿Qué AHT querés usar para calcular FTEs?",
                    ["Usar AHT promedio histórico", "Ingresar AHT manualmente (en segundos)"]
                )

                aht_personalizado = None
                if modo_aht == "Ingresar AHT manualmente (en segundos)":
                    aht_personalizado = st.number_input("⏱ AHT personalizado (segundos)", min_value=30, max_value=1800, value=350) # AHT 5 minutos y medio


                st.markdown("""
                    ℹ️ **¿Qué significan estos parámetros?**  
                    • **ASA:** Tiempo promedio de espera aceptable  
                    • **SLA:** % de llamadas que deben responderse dentro del ASA  
                    • **Shrinkage:** Tiempo no productivo de los agentes
                """)

                if st.button("🔁 Recalcular FTEs para todos los idiomas"):
                    resultados_fte = []

                    for idioma in idiomas:
                        df_filtrado = df_future[df_future["idioma"] == idioma].copy()
                        if df_filtrado.empty:
                            continue

                        cliente_actual = df_filtrado["cliente"].iloc[0] if "cliente" in df_filtrado.columns else "desconocido"

                        for _, row in df_filtrado.iterrows():
                            llamadas = row["pred"]
                            aht = aht_personalizado if aht_personalizado else row.get("aht", np.nan)


                            fte_result = None
                            if not pd.isna(aht) and llamadas > 0:
                                fte_result = estimar_fte_erlang_c(
                                    llamadas=llamadas,
                                    aht_segundos=aht,
                                    asa_segundos=asa,
                                    sla_pct=sla / 100,
                                    shrinkage_pct=shrinkage / 100
                                )

                            resultados_fte.append({
                                "date": row["date"],
                                "cliente": cliente_actual,
                                "idioma": idioma,
                                "llamadas_estimadas": round(llamadas),
                                "aht (seg)": round(aht, 2) if not pd.isna(aht) else None,
                                "fte_estimado": fte_result["fte_ajustado"] if fte_result else None,
                                "fte_neto": fte_result["fte_neto"] if fte_result else None,
                                "sla_estimado": fte_result["sla_estimado"] if fte_result else None,
                                "erlangs": fte_result["erlangs"] if fte_result else None
                            })

                    df_fte = pd.DataFrame(resultados_fte)
                    st.session_state["df_fte_resultado"] = df_fte

            with tabs[1]:
                df_fte = st.session_state.get("df_fte_resultado", None)

                if df_fte is not None and not df_fte["fte_estimado"].dropna().empty:
                    st.markdown("### 🧾 Estimación de FTEs por idioma")

                    # 📊 KPIs por idioma en formato tabla
                    df_resumen = (
                        df_fte.groupby("idioma")["fte_estimado"]
                        .agg(Mínimo="min", Máximo="max", Promedio="mean")
                        .reset_index()
                        .round(2)
                        .sort_values("Promedio", ascending=False)
                    )

                    # 🔢 Indicadores globales
                    fte_total = df_resumen["Promedio"].sum()
                    sla_promedio = df_fte["sla_estimado"].mean()

                    st.markdown("#### 📈 Indicadores globales")
                    col1, col2 = st.columns(2)
                    col1.metric("👥 Suma de FTE Promedios", f"{fte_total:.2f}")
                    col2.metric("📶 SLA Promedio Estimado", f"{sla_promedio:.1%}")

                    # 🧾 Tabla resumen por idioma
                    st.markdown("#### 📊 Resumen de FTEs estimados por idioma")
                    st.dataframe(df_resumen, use_container_width=True)

                    # 📋 Detalle por fecha
                    st.markdown("#### 📋 Detalle FTEs estimados por idioma y fecha")
                    st.dataframe(df_fte, use_container_width=True)

                    

                    # Verificamos si hay datos
                    if not df_fte.empty:
                        st.markdown("#### 📈 Evolución diaria de FTEs por idioma")

                        fig = px.line(
                            df_fte,
                            x="date",
                            y="fte_estimado",
                            color="idioma",
                            markers=True,
                            title="FTEs estimados por día e idioma",
                            labels={"date": "Fecha", "fte_estimado": "FTE estimado"}
                        )

                        fig.update_layout(
                            xaxis_title="Fecha",
                            yaxis_title="FTE estimado",
                            legend_title="Idioma",
                            hovermode="x unified",
                            height=500
                        )

                        st.plotly_chart(fig, use_container_width=True)


                    # 📥 Botón de descarga
                    csv_fte = df_fte.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Descargar todos los FTEs en CSV",
                        data=csv_fte,
                        file_name="fte_forecast_todos_idiomas.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("🔄 Generá los FTEs desde la pestaña anterior para ver resultados.")


