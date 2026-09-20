"""Coleta de notícias a partir de feeds RSS/Atom."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from time import mktime

import feedparser
import requests

from ..models import NewsItem

log = logging.getLogger(__name__)

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) OMatinal/1.0 Safari/537.36"
)


def _parse_published(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime.fromtimestamp(mktime(val), tz=timezone.utc)
            except (OverflowError, ValueError):
                continue
    return None


def _clean(text: str) -> str:
    """Remove tags HTML simples e normaliza espaços de um resumo."""
    import re

    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-zA-Z#0-9]+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fetch_feed(url: str, timeout: int = 20) -> feedparser.FeedParserDict:
    """Baixa o feed com requests (respeita proxy do ambiente) e parseia."""
    resp = requests.get(url, headers={"User-Agent": _UA}, timeout=timeout)
    resp.raise_for_status()
    return feedparser.parse(resp.content)


def coletar_categoria(
    categoria: str,
    fontes: list[dict[str, str]],
    limite_por_fonte: int = 12,
    janela_horas: int = 36,
) -> list[NewsItem]:
    """Coleta e ordena itens de todas as fontes de uma categoria."""
    itens: list[NewsItem] = []
    corte = None
    if janela_horas and janela_horas > 0:
        corte = datetime.now(timezone.utc) - timedelta(hours=janela_horas)

    for fonte in fontes:
        nome = fonte.get("nome", fonte.get("url", "?"))
        url = fonte.get("url")
        if not url:
            continue
        try:
            feed = _fetch_feed(url)
        except Exception as exc:  # noqa: BLE001
            log.warning("Falha ao ler feed %s (%s): %s", nome, url, exc)
            continue

        entries = feed.entries[:limite_por_fonte] if feed.entries else []
        for entry in entries:
            publicado = _parse_published(entry)
            if corte and publicado and publicado < corte:
                continue
            titulo = _clean(getattr(entry, "title", ""))
            if not titulo:
                continue
            resumo = _clean(getattr(entry, "summary", "") or getattr(entry, "description", ""))
            itens.append(
                NewsItem(
                    categoria=categoria,
                    fonte=nome,
                    titulo=titulo,
                    resumo=resumo[:600],
                    link=getattr(entry, "link", ""),
                    publicado=publicado,
                )
            )

    # dedupe por título (case-insensitive), mantendo o mais recente
    vistos: dict[str, NewsItem] = {}
    for item in itens:
        chave = item.titulo.lower()
        atual = vistos.get(chave)
        if atual is None or (item.publicado and (not atual.publicado or item.publicado > atual.publicado)):
            vistos[chave] = item

    ordenados = sorted(
        vistos.values(),
        key=lambda i: i.publicado or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return ordenados


def coletar_tudo(
    feeds: dict[str, list[dict[str, str]]],
    limite_por_fonte: int = 12,
    janela_horas: int = 36,
) -> dict[str, list[NewsItem]]:
    """Coleta todas as categorias definidas em `feeds`."""
    resultado: dict[str, list[NewsItem]] = {}
    for categoria, fontes in feeds.items():
        resultado[categoria] = coletar_categoria(
            categoria, fontes or [], limite_por_fonte, janela_horas
        )
        log.info("Categoria '%s': %d itens coletados", categoria, len(resultado[categoria]))
    return resultado
