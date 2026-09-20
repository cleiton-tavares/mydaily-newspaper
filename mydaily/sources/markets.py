"""Indicadores do dia (dólar, Ibovespa, Selic, bitcoin, IPCA) via APIs públicas.

Cada indicador tem um `fallback` no config: se a fonte online falhar, o jornal
sai mesmo assim com o último valor conhecido (marcado como defasado).
"""
from __future__ import annotations

import logging

import requests

from ..models import MarketNumber

log = logging.getLogger(__name__)

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OMatinal/1.0"


# --------------------------------------------------------------------------- #
#  Formatação numérica (padrão brasileiro: 1.234,56)
# --------------------------------------------------------------------------- #
def _br(value: float, decimals: int) -> str:
    s = f"{value:,.{decimals}f}"           # 1,234.56  (estilo en-US)
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _formatar(value: float, formato: str) -> str:
    if formato == "brl":
        return f"R$ {_br(value, 2)}"
    if formato == "usd":
        return f"US$ {_br(value, 2)}"
    if formato == "usd_compacto":
        if value >= 1000:
            return f"US$ {_br(value / 1000, 1)}k"
        return f"US$ {_br(value, 0)}"
    if formato == "brl_compacto":
        if value >= 1000:
            return f"R$ {_br(value / 1000, 1)}k"
        return f"R$ {_br(value, 0)}"
    if formato == "inteiro":
        return _br(value, 0)
    if formato == "percent":
        return f"{_br(value, 2)}%"
    return _br(value, 2)


def _delta(pct: float | None) -> tuple[str, str]:
    """Devolve (texto, trend)."""
    if pct is None:
        return ("—", "flat")
    if abs(pct) < 0.01:
        return ("estável", "flat")
    sinal = "+" if pct > 0 else "-"
    trend = "up" if pct > 0 else "down"
    return (f"{sinal}{_br(abs(pct), 1)}%", trend)


# --------------------------------------------------------------------------- #
#  Provedores
# --------------------------------------------------------------------------- #
def _awesomeapi(entry: dict) -> tuple[float, float | None]:
    code = entry["code"]                    # ex.: USD-BRL
    url = f"https://economia.awesomeapi.com.br/json/last/{code}"
    resp = requests.get(url, headers={"User-Agent": _UA}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    chave = code.replace("-", "")
    payload = data[chave]
    valor = float(payload["bid"])
    pct = payload.get("pctChange")
    return valor, (float(pct) if pct not in (None, "") else None)


def _bcb_sgs(entry: dict) -> tuple[float, float | None]:
    series = entry["series"]
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series}"
        "/dados/ultimos/2?formato=json"
    )
    resp = requests.get(url, headers={"User-Agent": _UA}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError("série vazia")
    valor = float(data[-1]["valor"])
    pct = None
    if len(data) >= 2:
        try:
            anterior = float(data[-2]["valor"])
            pct = valor - anterior         # variação em pontos percentuais
        except (ValueError, KeyError):
            pct = None
    return valor, pct


def _yahoo(entry: dict) -> tuple[float, float | None]:
    symbol = entry["symbol"]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    resp = requests.get(url, headers={"User-Agent": _UA}, timeout=15)
    resp.raise_for_status()
    meta = resp.json()["chart"]["result"][0]["meta"]
    valor = float(meta["regularMarketPrice"])
    anterior = meta.get("chartPreviousClose") or meta.get("previousClose")
    pct = None
    if anterior:
        pct = (valor - float(anterior)) / float(anterior) * 100
    return valor, pct


_PROVIDERS = {
    "awesomeapi": _awesomeapi,
    "bcb_sgs": _bcb_sgs,
    "yahoo": _yahoo,
}


def _um_numero(entry: dict) -> MarketNumber:
    label = entry.get("label", "?")
    formato = entry.get("formato", "brl")
    sem_delta = bool(entry.get("sem_delta"))
    fallback = str(entry.get("fallback", "—"))
    provider = entry.get("provider", "static")

    if provider == "static":
        return MarketNumber(label=label, valor=fallback, delta="—", sem_delta=True)

    fn = _PROVIDERS.get(provider)
    if fn is None:
        log.warning("Provedor desconhecido '%s' para %s", provider, label)
        return MarketNumber(label=label, valor=fallback, sem_delta=True, stale=True)

    try:
        valor, pct = fn(entry)
        texto = _formatar(valor, formato)
        if sem_delta:
            delta, trend = ("—", "flat")
        else:
            # para percentuais absolutos (Selic/IPCA) o delta em p.p. faz mais sentido
            if provider == "bcb_sgs" and pct is not None:
                if abs(pct) < 0.001:
                    delta, trend = ("estável", "flat")
                else:
                    sinal = "+" if pct > 0 else "-"
                    trend = "up" if pct > 0 else "down"
                    delta = f"{sinal}{_br(abs(pct), 2)} p.p."
            else:
                delta, trend = _delta(pct)
        sufixo = entry.get("sufixo", "")
        if sufixo:
            texto = f"{texto} {sufixo}".strip()
        return MarketNumber(label=label, valor=texto, delta=delta, trend=trend, sem_delta=sem_delta)
    except Exception as exc:  # noqa: BLE001
        log.warning("Falha ao obter '%s' (%s): %s — usando fallback", label, provider, exc)
        return MarketNumber(label=label, valor=fallback, delta="—", sem_delta=True, stale=True)


def obter_numeros(config_numeros: list[dict]) -> list[MarketNumber]:
    """Resolve todos os indicadores configurados."""
    return [_um_numero(entry) for entry in (config_numeros or [])]
