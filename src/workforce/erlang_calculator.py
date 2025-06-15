import math

def erlang_c_formula(erlangs, agentes):
    """Calcula la probabilidad de espera con Erlang C"""
    if agentes <= erlangs:
        return 1.0  # Saturado

    try:
        numerador = (erlangs ** agentes / math.factorial(agentes)) * (agentes / (agentes - erlangs))
        suma = sum((erlangs ** k) / math.factorial(k) for k in range(agentes))
        denominador = suma + numerador
        return numerador / denominador
    except (OverflowError, ZeroDivisionError):
        return 1.0  # si falla, asumir saturación total

def estimar_fte_erlang_c(
    llamadas,
    aht_segundos=300,
    asa_segundos=20,
    sla_pct=0.8,
    shrinkage_pct=0.3,
    intervalo_segundos=32400  # 🔧 corregido a jornada de 9 horas (1 día)
):
    """
    Estima los FTE necesarios usando Erlang C.
    """
    # 1. Calcular tráfico en Erlangs
    erlangs = (llamadas * aht_segundos) / intervalo_segundos
    erlangs = max(erlangs, 0.01)  # evitar división por 0

    # 2. Buscar mínimo número de agentes que cumplen SLA
    agentes = max(1, math.ceil(erlangs))
    sla_estimado = 0.0

    while agentes < 500:
        prob_espera = erlang_c_formula(erlangs, agentes)
        try:
            sla_estimado = 1 - (prob_espera * math.exp(-(agentes - erlangs) * (asa_segundos / aht_segundos)))
        except OverflowError:
            sla_estimado = 0.0

        if sla_estimado >= sla_pct:
            break
        agentes += 1

    # 3. Aplicar shrinkage
    fte_ajustado = math.ceil(agentes / (1 - shrinkage_pct))

    return {
        "fte_neto": agentes,
        "fte_ajustado": fte_ajustado,
        "erlangs": round(erlangs, 2),
        "sla_estimado": round(sla_estimado, 4)
    }
