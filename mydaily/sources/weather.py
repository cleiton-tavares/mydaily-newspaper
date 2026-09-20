"""Clima real via Open-Meteo (gratuito, sem chave de API)."""
from __future__ import annotations

import logging
from datetime import datetime

import requests

from ..models import HourForecast, Weather

log = logging.getLogger(__name__)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"

# Código WMO -> (texto pt-BR, chave de ícone lucide)
_WMO: dict[int, tuple[str, str]] = {
    0: ("Céu limpo", "sun"),
    1: ("Predomínio de sol", "sun"),
    2: ("Sol entre nuvens", "cloud-sun"),
    3: ("Nublado", "cloud"),
    45: ("Névoa", "cloud-fog"),
    48: ("Névoa com geada", "cloud-fog"),
    51: ("Garoa fraca", "cloud-drizzle"),
    53: ("Garoa", "cloud-drizzle"),
    55: ("Garoa intensa", "cloud-drizzle"),
    56: ("Garoa congelante", "cloud-drizzle"),
    57: ("Garoa congelante", "cloud-drizzle"),
    61: ("Chuva fraca", "cloud-rain"),
    63: ("Chuva", "cloud-rain"),
    65: ("Chuva forte", "cloud-rain"),
    66: ("Chuva congelante", "cloud-rain"),
    67: ("Chuva congelante", "cloud-rain"),
    71: ("Neve fraca", "cloud-snow"),
    73: ("Neve", "cloud-snow"),
    75: ("Neve forte", "cloud-snow"),
    77: ("Grãos de neve", "cloud-snow"),
    80: ("Pancadas de chuva", "cloud-rain"),
    81: ("Pancadas de chuva", "cloud-rain"),
    82: ("Pancadas fortes", "cloud-rain"),
    85: ("Pancadas de neve", "cloud-snow"),
    86: ("Pancadas de neve", "cloud-snow"),
    95: ("Trovoadas", "cloud-lightning"),
    96: ("Trovoadas com granizo", "cloud-lightning"),
    99: ("Trovoadas com granizo", "cloud-lightning"),
}

_DIRECOES = ["norte", "nordeste", "leste", "sudeste", "sul", "sudoeste", "oeste", "noroeste"]


def _wmo(code: int | None) -> tuple[str, str]:
    if code is None:
        return ("Tempo instável", "cloud-sun")
    return _WMO.get(int(code), ("Tempo variável", "cloud-sun"))


def _direcao(graus: float | None) -> str:
    if graus is None:
        return ""
    idx = int((graus % 360) / 45 + 0.5) % 8
    return _DIRECOES[idx]


def _hora_label(iso: str) -> str:
    # "2026-09-20T05:12" -> "05:12"
    try:
        return iso.split("T", 1)[1][:5]
    except (IndexError, AttributeError):
        return iso


def _icone_hora(code: int | None, hora: int) -> str:
    _, icon = _wmo(code)
    # amanhecer/entardecer viram ícones especiais quando o tempo está bom
    if icon in ("sun", "cloud-sun"):
        if hora <= 6:
            return "sunrise"
        if hora >= 18:
            return "sunset"
    return icon


def _fetch_marine(lat: float, lon: float, tz: str, timeout: int = 15) -> str:
    try:
        resp = requests.get(
            MARINE_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "wave_height_max",
                "timezone": tz,
                "forecast_days": 1,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        alturas = data.get("daily", {}).get("wave_height_max") or []
        if alturas and alturas[0] is not None:
            return f"Ondas até {alturas[0]:.1f} m".replace(".", ",")
    except Exception as exc:  # noqa: BLE001
        log.info("Clima marítimo indisponível: %s", exc)
    return ""


def obter_clima(cidade: str, lat: float, lon: float, tz: str) -> Weather:
    """Consulta o Open-Meteo e monta o objeto Weather. Nunca lança exceção."""
    try:
        resp = requests.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": (
                    "temperature_2m,relative_humidity_2m,apparent_temperature,"
                    "weather_code,wind_speed_10m,wind_direction_10m"
                ),
                "hourly": "temperature_2m,precipitation_probability,weather_code",
                "daily": (
                    "weather_code,temperature_2m_max,temperature_2m_min,"
                    "sunrise,sunset,uv_index_max,precipitation_probability_max"
                ),
                "timezone": tz,
                "forecast_days": 7,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        log.warning("Falha ao obter clima do Open-Meteo: %s", exc)
        return Weather(ok=False)

    cur = data.get("current", {})
    daily = data.get("daily", {})
    hourly = data.get("hourly", {})

    condicao, icon = _wmo(cur.get("weather_code"))

    def _t(v) -> str:
        return f"{round(v)}°" if v is not None else "—"

    maxima = daily.get("temperature_2m_max", [None])
    minima = daily.get("temperature_2m_min", [None])
    max_hoje = _t(maxima[0]) if maxima else "—"
    min_hoje = _t(minima[0]) if minima else "—"

    umidade = cur.get("relative_humidity_2m")
    sensacao = cur.get("apparent_temperature")
    vento = cur.get("wind_speed_10m")
    direcao = _direcao(cur.get("wind_direction_10m"))
    partes = []
    if sensacao is not None:
        partes.append(f"Sensação térmica {round(sensacao)}°")
    if umidade is not None:
        partes.append(f"Umidade {round(umidade)}%")
    if vento is not None:
        v = f"Vento {round(vento)} km/h"
        if direcao:
            v += f" de {direcao}"
        partes.append(v)
    linha_sensacao = " · ".join(partes)

    # previsão horária: pega 06,09,12,15,18,21 do dia atual
    horaria: list[HourForecast] = []
    times = hourly.get("temperature_2m") and hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    probs = hourly.get("precipitation_probability") or []
    codes = hourly.get("weather_code") or []
    if times:
        hoje = times[0].split("T", 1)[0]
        alvo = [6, 9, 12, 15, 18, 21]
        idx_por_hora: dict[int, int] = {}
        for i, t in enumerate(times):
            d, _, hm = t.partition("T")
            if d != hoje:
                continue
            h = int(hm[:2])
            if h in alvo and h not in idx_por_hora:
                idx_por_hora[h] = i
        for h in alvo:
            i = idx_por_hora.get(h)
            if i is None:
                continue
            horaria.append(
                HourForecast(
                    hora=f"{h:02d}h",
                    icon=_icone_hora(codes[i] if i < len(codes) else None, h),
                    temp=_t(temps[i]) if i < len(temps) else "—",
                    chuva=f"{round(probs[i])}%" if i < len(probs) and probs[i] is not None else "0%",
                )
            )

    # extras
    nascer = _hora_label(daily.get("sunrise", [""])[0]) if daily.get("sunrise") else ""
    por = _hora_label(daily.get("sunset", [""])[0]) if daily.get("sunset") else ""
    nascer_por = f"{nascer} / {por}" if nascer and por else ""

    uv_val = daily.get("uv_index_max", [None])
    uv = ""
    if uv_val and uv_val[0] is not None:
        v = round(uv_val[0])
        nivel = (
            "baixo" if v <= 2 else "moderado" if v <= 5 else "alto" if v <= 7 else "muito alto"
            if v <= 10 else "extremo"
        )
        uv = f"{v} · {nivel}"

    mar = _fetch_marine(lat, lon, tz)

    # resumo da semana (min/max dos próximos dias)
    semana = ""
    if len(maxima) >= 4 and maxima[1] is not None:
        mx = [m for m in maxima[1:6] if m is not None]
        mn = [m for m in minima[1:6] if m is not None]
        if mx and mn:
            semana = f"{round(min(mn))}° a {round(max(mx))}° nos próximos dias"

    prob_hoje = daily.get("precipitation_probability_max", [None])
    chuva_txt = ""
    if prob_hoje and prob_hoje[0] is not None:
        chuva_txt = f" · chuva {round(prob_hoje[0])}%"
    cond_curta = condicao.split(",")[0]
    resumo_curto = f"{cond_curta} · {min_hoje} / {max_hoje}{chuva_txt}"

    return Weather(
        temp_atual=_t(cur.get("temperature_2m")),
        icon=icon,
        condicao=condicao,
        maxima=max_hoje,
        minima=min_hoje,
        sensacao=_t(sensacao),
        umidade=f"{round(umidade)}%" if umidade is not None else "",
        vento=f"{round(vento)} km/h" if vento is not None else "",
        linha_sensacao=linha_sensacao,
        horaria=horaria,
        nascer_por_sol=nascer_por,
        indice_uv=uv,
        mar=mar,
        semana=semana,
        resumo_curto=resumo_curto,
        ok=True,
    )
