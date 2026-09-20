"""Montagem do contexto e renderização dos templates para HTML."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import Config
from .models import MarketNumber, Weather

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

_DIAS = [
    "SEGUNDA-FEIRA", "TERÇA-FEIRA", "QUARTA-FEIRA", "QUINTA-FEIRA",
    "SEXTA-FEIRA", "SÁBADO", "DOMINGO",
]
_DIAS_CURTO = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
_MESES = [
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
]
_MESES_CURTO = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]


def construir_meta(cfg: Config, hoje: date) -> dict[str, Any]:
    wd = hoje.weekday()
    ontem = hoje - timedelta(days=1)
    return {
        "titulo": cfg.jornal.get("titulo", "O Matinal"),
        "tagline": cfg.jornal.get("tagline", ""),
        "local": cfg.jornal.get("local", ""),
        "hora_impressao": cfg.jornal.get("hora_impressao", "05:30"),
        "ano_romano": cfg.jornal.get("ano_romano", "I"),
        "edicao_num": cfg.numero_edicao(hoje),
        "data_extenso": f"{_DIAS[wd]}, {hoje.day} DE {_MESES[hoje.month - 1]} DE {hoje.year}",
        "data_curta": f"{_DIAS_CURTO[wd]} · {hoje.day} {_MESES_CURTO[hoje.month - 1]}",
        "data_ontem": f"{ontem.day} DE {_MESES[ontem.month - 1]}",
    }


def montar_contexto(
    cfg: Config,
    editorial: dict[str, Any],
    weather: Weather,
    numeros: list[MarketNumber],
    hoje: date,
) -> dict[str, Any]:
    briefing = dict(editorial.get("briefing", {}))
    briefing["clima"] = weather.resumo_curto if weather and weather.resumo_curto else "—"
    return {
        "meta": construir_meta(cfg, hoje),
        "briefing": briefing,
        "ed": editorial,
        "weather": weather,
        "numeros": numeros,
        "agenda": cfg.agenda,
        "lembretes": cfg.lembretes,
        "clima_cidade": cfg.clima.get("cidade", ""),
    }


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2", "html.j2"], default_for_string=True),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def renderizar_html(contexto: dict[str, Any]) -> str:
    """Renderiza o documento HTML completo (as duas páginas)."""
    env = _env()
    tmpl = env.get_template("newspaper.html.j2")
    return tmpl.render(**contexto)
