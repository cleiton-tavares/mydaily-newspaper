"""Estruturas de dados usadas entre a coleta, a LLM e a renderização."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NewsItem:
    """Um item de notícia vindo de um feed RSS."""

    categoria: str          # "mundo" | "brasil" | "ia"
    fonte: str              # nome amigável do feed
    titulo: str
    resumo: str
    link: str
    publicado: Optional[datetime] = None

    def to_prompt_dict(self) -> dict[str, str]:
        return {
            "fonte": self.fonte,
            "titulo": self.titulo,
            "resumo": self.resumo,
            "publicado": self.publicado.strftime("%d/%m %H:%M") if self.publicado else "",
        }


@dataclass
class HourForecast:
    hora: str               # "06h"
    icon: str               # chave de ícone (ex.: "sun", "cloud-sun")
    temp: str               # "24°"
    chuva: str              # "10%"


@dataclass
class Weather:
    temp_atual: str = "—"
    icon: str = "cloud-sun"
    condicao: str = ""
    maxima: str = ""
    minima: str = ""
    sensacao: str = ""
    umidade: str = ""
    vento: str = ""
    linha_sensacao: str = ""          # "Sensação térmica 29° · Umidade 74% · Vento 18 km/h"
    horaria: list[HourForecast] = field(default_factory=list)
    nascer_por_sol: str = ""
    indice_uv: str = ""
    mar: str = ""
    semana: str = ""
    resumo_curto: str = ""            # usado na barra de briefing da capa
    ok: bool = False                  # False = usou fallback/placeholder


@dataclass
class Comic:
    """A tira de quadrinhos do dia (buscada da fonte do autor)."""

    ok: bool = False
    image_data_uri: str = ""       # data:image/...;base64,...
    titulo: str = ""
    autor: str = ""
    fonte: str = ""                # domínio da fonte (crédito)
    data: str = ""                 # data formatada da publicação
    link: str = ""


@dataclass
class MarketNumber:
    label: str
    valor: str
    delta: str = "—"
    trend: str = "flat"               # "up" | "down" | "flat"
    sem_delta: bool = False
    stale: bool = False               # True = veio do fallback
