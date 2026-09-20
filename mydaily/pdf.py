"""Geração do PDF a partir do HTML usando o Chromium (Playwright)."""
from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

# O design de cada folha tem 1240x1754 px (A4 @150dpi). Reduzir por este fator
# encaixa exatamente em uma página A4 (210x297mm @96dpi = 793.7x1122.5 px).
A4_SCALE = 0.6406


def _proxy_do_ambiente() -> dict | None:
    """Se houver proxy no ambiente, repassa ao Chromium (útil atrás de proxy)."""
    server = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy") or os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    if server:
        return {"server": server}
    return None


def html_para_pdf(
    html: str,
    pdf_path: str | os.PathLike[str],
    chromium_path: str | None = None,
    espera_rede_ms: int = 1200,
) -> Path:
    """Renderiza o HTML e grava o PDF de duas páginas A4. Requer internet
    (Tailwind CDN + Google Fonts) no momento da renderização."""
    from playwright.sync_api import sync_playwright

    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    launch_kwargs: dict = {}
    if chromium_path:
        launch_kwargs["executable_path"] = chromium_path
    proxy = _proxy_do_ambiente()
    if proxy:
        launch_kwargs["proxy"] = proxy

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.set_content(html, wait_until="networkidle")
        # Espera as fontes carregarem (melhora bastante o resultado impresso).
        try:
            page.wait_for_function(
                "document.fonts && document.fonts.status === 'loaded'", timeout=8000
            )
        except Exception:  # noqa: BLE001
            log.info("Fontes não sinalizaram carregamento; seguindo mesmo assim.")
        page.wait_for_timeout(espera_rede_ms)

        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            scale=A4_SCALE,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        context.close()
        browser.close()

    log.info("PDF gerado em %s", pdf_path)
    return pdf_path


def contar_paginas(pdf_path: str | os.PathLike[str]) -> int:
    """Conta páginas do PDF sem depender de libs pesadas (regex no conteúdo)."""
    import re

    data = Path(pdf_path).read_bytes()
    # Conta objetos /Type /Page (mas não /Pages).
    return len(re.findall(rb"/Type\s*/Page[^s]", data)) or len(re.findall(rb"/Type/Page[^s]", data))
