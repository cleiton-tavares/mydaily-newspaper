"""Interface de linha de comando e orquestração do pipeline."""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime

from . import __version__
from .config import Config, load_config, require_llm_credentials
from .render import construir_meta, montar_contexto, renderizar_html

log = logging.getLogger("mydaily")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="mydaily",
        description="O Matinal — gera e imprime seu jornal matinal personalizado.",
    )
    p.add_argument("--config", metavar="PATH", help="caminho do config.yaml")
    p.add_argument("--demo", action="store_true",
                   help="usa conteúdo de exemplo (sem internet nem LLM) para pré-visualizar o layout")
    p.add_argument("--no-print", action="store_true", help="gera o PDF mas não imprime")
    p.add_argument("--no-pdf", action="store_true", help="gera apenas o HTML (não gera PDF nem imprime)")
    p.add_argument("--dry-run-print", action="store_true", help="simula a impressão (não envia à impressora)")
    p.add_argument("--date", metavar="YYYY-MM-DD", help="força a data do jornal (padrão: hoje)")
    p.add_argument("--printer", metavar="NOME", help="sobrescreve a impressora do config")
    p.add_argument("-v", "--verbose", action="store_true", help="log detalhado")
    p.add_argument("--version", action="version", version=f"O Matinal {__version__}")
    return p.parse_args(argv)


def _hoje(args: argparse.Namespace, cfg: Config) -> date:
    if args.date:
        return datetime.strptime(args.date, "%Y-%m-%d").date()
    return datetime.now(cfg.tz).date()


def _coletar_conteudo(cfg: Config, hoje: date, demo: bool):
    """Devolve (editorial, weather, numeros)."""
    from . import sample

    if demo:
        log.info("Modo demo: usando conteúdo de exemplo.")
        return sample.editorial_exemplo(), sample.weather_exemplo(), sample.numeros_exemplo()

    # Credenciais da LLM são obrigatórias fora do modo demo.
    faltando = require_llm_credentials(cfg)
    if faltando:
        raise SystemExit(
            "Faltam credenciais do LiteLLM: " + ", ".join(faltando) + ".\n"
            "Preencha o arquivo .env (veja .env.example) ou rode com --demo para "
            "apenas pré-visualizar o layout."
        )

    from .sources import markets, rss, weather as weather_src
    from .llm import gerar_editorial

    log.info("Coletando notícias (RSS)...")
    noticias = rss.coletar_tudo(
        cfg.feeds,
        limite_por_fonte=cfg.raw.get("feeds_limite_por_fonte", 12),
        janela_horas=cfg.raw.get("feeds_janela_horas", 36),
    )
    total = sum(len(v) for v in noticias.values())
    log.info("Total de %d notícias coletadas.", total)
    if total == 0:
        raise SystemExit("Nenhuma notícia foi coletada. Verifique os feeds e a conexão.")

    log.info("Consultando clima (Open-Meteo)...")
    clima = cfg.clima
    weather = weather_src.obter_clima(
        clima.get("cidade", ""),
        float(clima.get("latitude", 0.0)),
        float(clima.get("longitude", 0.0)),
        clima.get("fuso", cfg.jornal.get("fuso", "America/Sao_Paulo")),
    )

    log.info("Consultando indicadores do dia...")
    numeros = markets.obter_numeros(cfg.numeros)

    data_str = construir_meta(cfg, hoje)["data_extenso"]
    log.info("Gerando o conteúdo editorial via LiteLLM (modelo: %s)...", cfg.llm.model)
    editorial = gerar_editorial(cfg, noticias, data_str)
    return editorial, weather, numeros


def run(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    cfg = load_config(args.config)
    hoje = _hoje(args, cfg)
    print(f"O Matinal — edição de {hoje.isoformat()}")

    editorial, weather, numeros = _coletar_conteudo(cfg, hoje, args.demo)

    contexto = montar_contexto(cfg, editorial, weather, numeros, hoje)
    html = renderizar_html(contexto)

    out_dir = cfg.output_dir
    base = f"o-matinal-{hoje.isoformat()}"
    html_path = out_dir / f"{base}.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"  HTML: {html_path}")

    if args.no_pdf:
        print("  (PDF e impressão pulados por --no-pdf)")
        return 0

    from .pdf import contar_paginas, html_para_pdf

    pdf_path = out_dir / f"{base}.pdf"
    print("  Gerando PDF (Chromium)...")
    html_para_pdf(html, pdf_path, chromium_path=cfg.llm.chromium_path)
    try:
        paginas = contar_paginas(pdf_path)
    except Exception:  # noqa: BLE001
        paginas = -1
    print(f"  PDF:  {pdf_path}" + (f" ({paginas} páginas)" if paginas > 0 else ""))

    if args.no_print:
        print("  (impressão pulada por --no-print)")
        return 0

    from .printing import imprimir

    impressao = cfg.impressao
    impressora = args.printer if args.printer is not None else impressao.get("impressora", "")
    resultado = imprimir(
        pdf_path,
        impressora=impressora or "",
        copias=int(impressao.get("copias", 1)),
        sumatra_path=impressao.get("sumatra_path") or None,
        dry_run=args.dry_run_print,
    )
    marca = "OK" if resultado.ok else "FALHA"
    print(f"  Impressão [{marca}]: {resultado.mensagem}")
    return 0 if resultado.ok else 2


def main() -> None:
    try:
        sys.exit(run())
    except KeyboardInterrupt:
        print("\nInterrompido.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
