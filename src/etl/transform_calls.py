import pandas as pd
import os
from pathlib import Path
import re

def parse_timedelta_to_seconds(val):
    try:
        return pd.to_timedelta(val).total_seconds()
    except:
        return None

def procesar_llamadas():
    root_dir = Path(__file__).resolve().parents[2]
    input_path = root_dir / "data" / "interim" / "datos_llamadas.csv"
    output_path = root_dir / "data" / "processed" / "llamadas_diarias.csv"

    df = pd.read_csv(input_path)

    # Normalizar nombres de columnas
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]

    # Convertir AHT desde string/timedelta a segundos
    if "aht" in df.columns:
        df["aht"] = df["aht"].apply(parse_timedelta_to_seconds)

    # Convertir otros campos opcionales si querés conservarlos
    if "talk_(avg)" in df.columns:
        df["talk_avg"] = df["talk_(avg)"].apply(parse_timedelta_to_seconds)

    # Crear columna 'date' y filtrar solo días hábiles
    df["date"] = pd.to_datetime(df["date_time"]).dt.date
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.weekday < 5]

    # Calcular AHT promedio por cliente + idioma
    df_aht_promedio = df.groupby(["cliente", "idioma"])["aht"].mean().reset_index()

    # Agrupación diaria de llamadas ofrecidas
    df_grouped = df.groupby(["date", "cliente", "idioma"]).agg({"offered": "sum"}).reset_index()
    df_grouped.rename(columns={"offered": "y"}, inplace=True)

    # Agregar AHT promedio
    df_grouped = df_grouped.merge(df_aht_promedio, on=["cliente", "idioma"], how="left")

    # Agregar features
    df_grouped["dayofweek"] = df_grouped["date"].dt.dayofweek
    df_grouped["is_month_end"] = df_grouped["date"].dt.is_month_end.astype(int)

    # Crear lags
    df_grouped = df_grouped.sort_values(["cliente", "idioma", "date"])
    for lag in [1, 2, 3, 4, 5]:
        df_grouped[f"lag_{lag}"] = df_grouped.groupby(["cliente", "idioma"])["y"].shift(lag)

    # Filtrar filas sin lags
    lag_cols = [f"lag_{i}" for i in range(1, 6)]
    df_grouped.dropna(subset=lag_cols, inplace=True)

    # Guardar archivo final
    os.makedirs(output_path.parent, exist_ok=True)
    df_grouped.to_csv(output_path, index=False)
    print(f"✅ Dataset procesado guardado en {output_path}")

    return df_grouped
