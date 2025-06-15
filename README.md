# InLine - Predicción y planificación inteligente para contact centers

**InLine** 
Es una herramienta de inteligencia operativa desarrollada como proyecto final del Máster en Data Science e Inteligencia Artificial. 
Su propósito es mejorar la planificación de recursos en contact centers a través de modelos de predicción del volumen de llamadas y estimación de los recursos humanos necesarios utilizando la fórmula de Erlang C.


## Link app: Network URL: http://192.168.1.130:8501

---

## 🎯 Objetivos del Proyecto

- Predecir la demanda de llamadas entrantes por idioma y cliente utilizando modelos de series temporales (XGBoost).
- Estimar la cantidad de agentes (FTEs) requeridos para alcanzar un nivel de servicio deseado aplicando la fórmula de Erlang C.
- Permitir la visualización y exploración de los resultados a través de una interfaz desarrollada en Streamlit.

---

## 🧠 Técnicas y Herramientas Utilizadas

- **Lenguaje**: Python 3.12
- **Librerías clave**: `pandas`, `numpy`, `xgboost`, `scikit-learn`, `matplotlib`, `plotly`, `streamlit`
- **Modelado**: Series temporales con XGBoost (predicción día a día)
- **Estimación de capacidad**: Fórmula de Erlang C adaptada a distintos niveles de ASA/AHT
- **Interfaz visual**: Streamlit, con navegación por pestañas, selección de cliente, idioma y fechas

---

## 🗃️ Estructura del Proyecto

proyecto_final/
│
├── app/
│   ├── streamlit_app.py      # App principal
│   └── home.py               # Página de inicio
│
├── images/                   # Estetica del proyecto/banner/resultados de Modelos/GIF de funcionalidad
│   
├── pitch/                    # Pista de audio del Pitch + banner
│
├── src/
│   ├── forecast/             # Lógica de predicción
│   ├── workforce/            # Cálculo de FTEs con Erlang C
│   └── utils/                # Funciones auxiliares
│
├── data/
│   ├── raw/                  # Datos originales
│   └── processed/            # Datos limpios y filtrados
│
├── models/                   # Modelos entrenados y métricas
├── README.md
├── requirements.txt
└── .gitignore

---

## 🚀 ¿Cómo ejecutar el proyecto?

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/tuusuario/proyecto_inline.git
   cd proyecto_inline
   ```

2. **Crear un entorno virtual (opcional pero recomendado)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**:
   ```bash
   streamlit run app/streamlit_app.py
   ```

---

## 📊 Funcionalidades disponibles

- **Forecast por cliente e idioma**: selección dinámica de cliente, idioma y fechas.
- **Visualización de métricas del modelo**: MAE, RMSE, IC 95%.
- **Estimación de FTEs requeridos**: cálculo por idioma o todos a la vez según nivel de servicio (ASA) y duración media de llamada (AHT).
- **Gráficos interactivos** con Plotly para evolución de llamadas y FTEs.

---

## 📌 Consideraciones adicionales

- El forecast se realiza únicamente sobre días laborables (lunes a viernes).
- El cálculo de Erlang permite modificar parámetros como ASA deseado y AHT para simular distintos escenarios.
- La app permite recalcular dinámicamente la necesidad de recursos con sliders.


---

## 🏁 Estado del Proyecto

✅ Finalizado y funcional  
🛠️ Posibles mejoras futuras y escalabilidad:
- Integración con bases de datos directo a API de telefonia
- Forecast a nivel de 15 minutos
- Optimización de asignación multiskill
- Escalabilidad 


---

## 🎤Elevator Pitch


Planificar sin datos es arriesgar el servicio. Y esto, hoy, sigue ocurriendo en nuestro contact center.
Actualmente trabajamos con un error de predicción del 30 %, con jornadas donde el SLA cae por debajo del 70 %, muy lejos del objetivo comercial del 80 %.
Esto genera sobrecostes, presión innecesaria sobre los equipos y una experiencia insatisfactoria para el cliente.
La oportunidad está en prever con precisión, actuar con anticipación y decidir mejor.

Para responder a ese desafío, he creado InLine, una herramienta web, simple y personalizable, que predice el volumen diario de llamadas por idioma y calcula automáticamente la cantidad de agentes necesarios para cada jornada.
Está pensada para responsables operativos: permite seleccionar cliente, idioma y rango de fechas, y en cuestión de segundos devuelve tanto el forecast como la planificación óptima.
Los modelos fueron entrenados con más de un año de datos reales. Reducimos el error de predicción al 10 %, y al 8 % en idiomas clave, mejorando significativamente la asignación de recursos y el cumplimiento del SLA.
Además, la herramienta permite comparar escenarios, anticipar cambios operativos, ver cómo evoluciona la necesidad de personal y exportar la planificación de forma inmediata.
InLine no solo prevé: impulsa decisiones, reduce incertidumbre y mejora la operación.

Hoy puede utilizarse de forma interna, pero está listo para escalar a otros equipos de atención en España y Europa.
Y a diferencia de soluciones genéricas, InLine modela por cliente, idioma y día hábil, capturando los patrones reales de la demanda con máxima precisión.
Porque InLine no solo mejora la planificación: convierte la incertidumbre del dia a dia en confianza operativa.

---

## 👤 Autor

**Gonzalo Joaquín Casco**  
📍 Alcalá de Henares, España  
📧 gcasco91@gmail.com  
💼 [LinkedIn](https://www.linkedin.com/in/gonzalo-casco/)
