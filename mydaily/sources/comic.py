"""Busca a tira de quadrinhos do dia da fonte do autor (ex.: Will Tirando).

O app baixa a imagem publicada pelo autor e a embute no jornal pessoal do
usuário, sempre creditando a fonte. Ele NÃO redesenha nem altera a arte —
apenas referencia a imagem original publicada. Respeite o direito autoral do
autor: o jornal é para uso pessoal.
"""
from __future__ import annotations

import base64
import logging
import re
from datetime import datetime
from time import mktime

import requests

from ..models import Comic

log = logging.getLogger(__name__)

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) OMatinal/1.0 Safari/537.36"
)
_IMG_RE = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)
_OG_RE = re.compile(
    r"<meta[^>]+property=[\"']og:image[\"'][^>]+content=[\"']([^\"']+)[\"']", re.IGNORECASE
)
_MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

# Tamanho máximo da imagem embutida (evita PDFs gigantes).
_MAX_BYTES = 6 * 1024 * 1024


def _dominio(url: str) -> str:
    m = re.match(r"https?://([^/]+)/?", url or "")
    dom = m.group(1) if m else (url or "")
    return dom[4:] if dom.startswith("www.") else dom


def _data_extenso(dt: datetime | None) -> str:
    if not dt:
        return ""
    return f"{dt.day} {_MESES[dt.month - 1]} {dt.year}"


def _baixar_imagem(url: str) -> str:
    resp = requests.get(url, headers={"User-Agent": _UA}, timeout=25)
    resp.raise_for_status()
    conteudo = resp.content
    if len(conteudo) > _MAX_BYTES:
        raise ValueError(f"imagem muito grande ({len(conteudo)} bytes)")
    ctype = resp.headers.get("Content-Type", "").split(";")[0].strip()
    if not ctype or not ctype.startswith("image/"):
        # deduz pela extensão
        ext = url.rsplit(".", 1)[-1].lower()
        ctype = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                 "gif": "image/gif", "webp": "image/webp"}.get(ext, "image/jpeg")
    b64 = base64.b64encode(conteudo).decode("ascii")
    return f"data:{ctype};base64,{b64}"


def _url_via_feed(feed_url: str) -> tuple[str, str, datetime | None, str]:
    """Devolve (img_url, titulo, data, link) a partir do feed RSS."""
    import feedparser

    resp = requests.get(feed_url, headers={"User-Agent": _UA}, timeout=25)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)
    if not feed.entries:
        raise ValueError("feed sem itens")
    entry = feed.entries[0]

    html = ""
    if entry.get("content"):
        html = entry["content"][0].get("value", "")
    if not html:
        html = entry.get("summary", "") or entry.get("description", "")
    m = _IMG_RE.search(html or "")
    if not m:
        raise ValueError("nenhuma imagem no item do feed")
    img_url = m.group(1)

    publicado = None
    for attr in ("published_parsed", "updated_parsed"):
        val = entry.get(attr)
        if val:
            try:
                publicado = datetime.fromtimestamp(mktime(val))
                break
            except (OverflowError, ValueError):
                pass
    return img_url, entry.get("title", "").strip(), publicado, entry.get("link", "")


def _url_via_og(site_url: str) -> tuple[str, str, datetime | None, str]:
    """Fallback: pega a og:image da home."""
    resp = requests.get(site_url, headers={"User-Agent": _UA}, timeout=25)
    resp.raise_for_status()
    m = _OG_RE.search(resp.text)
    if not m:
        raise ValueError("og:image não encontrada")
    return m.group(1), "", None, site_url


def obter_quadrinho(
    feed_url: str = "",
    site_url: str = "",
    autor: str = "",
) -> Comic:
    """Busca a tira do dia. Nunca lança exceção — devolve Comic(ok=False) em falha."""
    fonte = _dominio(feed_url or site_url)
    try:
        img_url = titulo = link = ""
        publicado = None
        if feed_url:
            try:
                img_url, titulo, publicado, link = _url_via_feed(feed_url)
            except Exception as exc:  # noqa: BLE001
                log.info("Quadrinho via feed falhou (%s); tentando og:image.", exc)
        if not img_url and site_url:
            img_url, titulo, publicado, link = _url_via_og(site_url)
        if not img_url:
            raise ValueError("não foi possível localizar a imagem da tira")

        data_uri = _baixar_imagem(img_url)
        return Comic(
            ok=True,
            image_data_uri=data_uri,
            titulo=titulo,
            autor=autor or "",
            fonte=fonte,
            data=_data_extenso(publicado),
            link=link or site_url or feed_url,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("Falha ao buscar o quadrinho do dia: %s", exc)
        return Comic(ok=False, autor=autor or "", fonte=fonte)
