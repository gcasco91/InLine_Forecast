import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

def forecast_idioma(df, idioma, cliente, fecha_inicio="2025-01-01"):
    # Validación inicial
    if df.empty or idioma not in df["idioma"].unique():
        return None, None, None

    # Filtrado por idioma, cliente y días hábiles
    idioma = [idioma] if isinstance(idioma, str) else idioma
    df_idioma = df[df["idioma"].isin(idioma) & df["cliente"].isin(cliente)].copy()
    df_idioma = df_idioma[df_idioma["date"].dt.dayofweek < 5]

    # Suavizado
    serie = df_idioma.set_index("date")["y"].resample("D").sum().fillna(0)
    serie_suavizada = serie.rolling(window=3, center=True).mean().dropna()
    serie_ultimos = serie_suavizada[serie_suavizada.index >= fecha_inicio]

    # Features + lags
    df_feat = serie_ultimos.reset_index()
    df_feat.columns = ["date", "y"]
    df_feat["dayofweek"] = df_feat["date"].dt.dayofweek
    df_feat["is_month_end"] = df_feat["date"].dt.is_month_end.astype(int)

    for lag in [1, 2, 3, 4, 5]:
        df_feat[f"lag_{lag}"] = df_feat["y"].shift(lag)

    df_feat.dropna(inplace=True)
    df_feat.set_index("date", inplace=True)

    # Split dinámico: últimos 30 días hábiles como test
    dias_habiles = df_feat.index[df_feat.index.dayofweek < 5]
    if len(dias_habiles) < 31:
        return None, None, None

    fecha_split = dias_habiles[-30]

    X = df_feat.drop(columns="y")
    y = df_feat["y"]
    X_train = X[X.index < fecha_split]
    y_train = y[y.index < fecha_split]
    X_test = X[X.index >= fecha_split]
    y_test = y[y.index >= fecha_split]

    # Volver a asegurar días hábiles solo en test
    X_test = X_test[X_test.index.dayofweek < 5]
    y_test = y_test[y_test.index.dayofweek < 5]

    if X_train.empty or X_test.empty:
        return None, None, None

    # Outlier puntual
    outlier_date = pd.Timestamp("2025-04-21")
    if outlier_date in y_test.index:
        entorno = y_test.loc["2025-04-16":"2025-04-25"].drop(index=outlier_date)
        y_test.loc[outlier_date] = entorno.mean()

    # Modelo
    model = XGBRegressor(n_estimators=50, learning_rate=0.1, random_state=42)
    model.fit(X_train, y_train)

    # Predicción + IC
    y_pred = pd.Series(model.predict(X_test), index=X_test.index)
    resid = y_test - y_pred
    std_err = resid.std()
    ci_sup = y_pred + 1.96 * std_err
    ci_inf = np.clip(y_pred - 1.96 * std_err, a_min=0, a_max=None)

    # Aplicar filtro final para evitar fines de semana en la salida
    mask_habiles = X_test.index.dayofweek < 5
    X_test = X_test[mask_habiles]
    y_test = y_test[mask_habiles]
    y_pred = y_pred[mask_habiles]
    ci_inf = ci_inf[mask_habiles]
    ci_sup = ci_sup[mask_habiles]


    # Output
    df_out = pd.DataFrame({
        "date": X_test.index,
        "real": y_test.values,
        "pred": y_pred.values,
        "ic_95_inf": ci_inf,
        "ic_95_sup": ci_sup
    })

    metricas = {
        "MAE": round(mean_absolute_error(y_test, y_pred), 2),
        "RMSE": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
        "MAPE": round(np.mean(np.abs((y_test - y_pred) / y_test.replace(0, np.nan))) * 100, 2)
    }
    df_out = df_out[df_out["date"].dt.dayofweek < 5]
    
    # Agregamos aht por combinación cliente+idioma si está en df original
    aht_prom = df_idioma["aht"].mean() if "aht" in df_idioma.columns else np.nan
    df_out["aht"] = aht_prom

    return df_out, model, metricas
