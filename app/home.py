import streamlit as st
import pandas as pd
import os
import base64

def get_base64_of_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def home():
    # ✅ Definir root_path primero
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # ✅ Ruta y conversión del logo
    logo_path = os.path.join(root_path, "images", "InLine-logoOnly.png")
    logo_base64 = get_base64_of_image(logo_path)

    # ✅ Mostrar logo + título en fila
    st.markdown(
        f"""
        <div style="text-align: center;">
            <img src="data:image/png;base64,{logo_base64}" width="480"/>
            <h1 style="margin-top: 0.5rem;">Predicción y planificación inteligente para contact centers</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ✅ Fondo con imagen + overlay blanco
    ruta_imagen = os.path.join(root_path, "images", "proyeccion-de-llamadas-en-call-center.jpg")

    if os.path.exists(ruta_imagen):
        img_base64 = get_base64_of_image(ruta_imagen)
        st.markdown(
            f"""
            <style>
            .stApp {{
                position: relative;
                background-image: url("data:image/jpg;base64,{img_base64}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            .stApp::before {{
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(255, 255, 255, 0.9);
                z-index: 0;
            }}
            .stApp > * {{
                position: relative;
                z-index: 1;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("⚠️ No se encontró la imagen de fondo.")

    # ✅ Contenido principal
    st.markdown("""
    **Bienvenido al panel de predicción de llamadas y estimación de FTEs necesarios.**

    ---
    **¿Qué podés hacer desde aquí?**
    - Subir el archivo base de llamadas en Excel
    - Transformarlo automáticamente
    - Ver una vista previa de los datos listos para el análisis

    📌 **Asegurate de que tu archivo contenga columnas como: `fecha`, `cliente`, `idioma`, `aht`, `llamadas`.**

    ---
    """)

    st.markdown("### 📁 Subí tu archivo Excel")
    uploaded_file = st.file_uploader("Seleccioná un archivo con datos de llamadas", type=["xlsx"])

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)

            st.success("✅ Archivo cargado correctamente")
            st.subheader("👀 Vista previa de los datos originales")
            st.dataframe(df.head())

            # Limpieza de nombres
            df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

            # Validación clave
            if "cliente" not in df.columns:
                st.error("❌ Falta la columna 'cliente'. Verificá el archivo.")
                st.stop()

            # Guardar archivo en data/interim
            interim_path = os.path.join(root_path, "data", "interim", "datos_llamadas.csv")
            os.makedirs(os.path.dirname(interim_path), exist_ok=True)
            df.to_csv(interim_path, index=False)
            st.info("📥 Datos guardados en `data/interim/datos_llamadas.csv`")

            # Ejecutar transformación
            from src.etl.transform_calls import procesar_llamadas
            df_transformado = procesar_llamadas()

            st.success("✅ Datos transformados correctamente y listos para el forecast.")
            st.subheader("🧪 Vista previa de datos transformados")
            st.dataframe(df_transformado.head())

            return df_transformado

        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {e}")

    else:
        st.info("⬆️ Esperando que subas un archivo para continuar.")

    return None
