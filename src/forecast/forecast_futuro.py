import pandas as pd
import numpy as np
from datetime import timedelta

def forecast_futuro(model, df_hist, n_dias=20):
    # Asegurarse de que el índice sea datetime
    df_hist = df_hist.copy()
    df_hist.index = pd.to_datetime(df_hist.index)

    # Usar solo fechas hábiles
    df_hist = df_hist[df_hist.index.dayofweek < 5]

    # Crear base futura
    last_date = df_hist.index.max()
    future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=n_dias*2, freq='B')
    future_dates = future_dates[:n_dias]  # solo n_dias hábiles

    future_df = pd.DataFrame(index=future_dates)
    future_df["dayofweek"] = future_df.index.dayofweek
    future_df["is_month_end"] = future_df.index.is_month_end.astype(int)

    # Copia de la serie histórica para construir lags en cascada
    lag_base = df_hist["y"].copy()
    future_preds = []

    for fecha in future_df.index:
        lags = [lag_base[-i] for i in [1, 2, 3, 4, 5]]
        features = {
            "dayofweek": fecha.dayofweek,
            "is_month_end": int(fecha.is_month_end),
            "lag_1": lags[0],
            "lag_2": lags[1],
            "lag_3": lags[2],
            "lag_4": lags[3],
            "lag_5": lags[4],
        }
        X_new = pd.DataFrame([features])
        y_pred = model.predict(X_new)[0]
        lag_base.loc[fecha] = y_pred  # actualizar serie para siguientes lags
        future_preds.append(y_pred)

    # Calcular IC 95% usando std de residuos recientes como estimación
    resid_std = df_hist["y"].std()
    ic_95_inf = np.clip(np.array(future_preds) - 1.96 * resid_std, a_min=0, a_max=None)
    ic_95_sup = np.array(future_preds) + 1.96 * resid_std

    df_futuro = pd.DataFrame({
        "date": future_df.index,
        "pred": future_preds,
        "ic_95_inf": ic_95_inf,
        "ic_95_sup": ic_95_sup
    })

    return df_futuro.reset_index(drop=True)
