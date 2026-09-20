"""Impressão do PDF final. Foco em Windows, com fallback CUPS (Linux/macOS)."""
from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


class ResultadoImpressao:
    def __init__(self, ok: bool, mensagem: str):
        self.ok = ok
        self.mensagem = mensagem

    def __bool__(self) -> bool:  # permite `if resultado:`
        return self.ok


# --------------------------------------------------------------------------- #
#  Windows
# --------------------------------------------------------------------------- #
def _achar_sumatra(caminho_config: str | None) -> str | None:
    candidatos: list[str] = []
    if caminho_config:
        candidatos.append(caminho_config)
    localappdata = os.getenv("LOCALAPPDATA", "")
    programfiles = os.getenv("PROGRAMFILES", r"C:\Program Files")
    programfiles86 = os.getenv("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
    candidatos += [
        str(Path(programfiles) / "SumatraPDF" / "SumatraPDF.exe"),
        str(Path(programfiles86) / "SumatraPDF" / "SumatraPDF.exe"),
        str(Path(localappdata) / "SumatraPDF" / "SumatraPDF.exe"),
    ]
    for c in candidatos:
        if c and Path(c).is_file():
            return c
    achado = shutil.which("SumatraPDF") or shutil.which("SumatraPDF.exe")
    return achado


def _imprimir_windows(pdf: Path, impressora: str, copias: int, sumatra: str | None) -> ResultadoImpressao:
    sumatra_exe = _achar_sumatra(sumatra)
    if sumatra_exe:
        base = [sumatra_exe, "-silent", "-exit-when-done"]
        if impressora:
            base += ["-print-to", impressora]
        else:
            base += ["-print-to-default"]
        base.append(str(pdf))
        for i in range(max(1, copias)):
            log.info("Imprimindo (SumatraPDF) cópia %d/%d...", i + 1, copias)
            proc = subprocess.run(base, capture_output=True, text=True)
            if proc.returncode != 0:
                return ResultadoImpressao(
                    False, f"SumatraPDF retornou código {proc.returncode}: {proc.stderr.strip()}"
                )
        alvo = impressora or "impressora padrão"
        return ResultadoImpressao(True, f"Enviado para {alvo} via SumatraPDF ({copias} cópia(s)).")

    # Fallback: PowerShell Start-Process com o verbo de impressão do app padrão.
    log.info("SumatraPDF não encontrado; usando o visualizador de PDF padrão via PowerShell.")
    if impressora:
        ps = (
            f"Start-Process -FilePath '{pdf}' -Verb PrintTo "
            f"-ArgumentList '\"{impressora}\"'"
        )
    else:
        ps = f"Start-Process -FilePath '{pdf}' -Verb Print"
    for _ in range(max(1, copias)):
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True
        )
        if proc.returncode != 0:
            return ResultadoImpressao(False, f"PowerShell falhou: {proc.stderr.strip()}")
    return ResultadoImpressao(
        True,
        "Enviado ao visualizador de PDF padrão via PowerShell. "
        "Dica: instale o SumatraPDF para impressão silenciosa e mais confiável.",
    )


# --------------------------------------------------------------------------- #
#  CUPS (Linux / macOS)
# --------------------------------------------------------------------------- #
def _imprimir_cups(pdf: Path, impressora: str, copias: int) -> ResultadoImpressao:
    lp = shutil.which("lp") or shutil.which("lpr")
    if not lp:
        return ResultadoImpressao(False, "Comando 'lp'/'lpr' não encontrado (CUPS não instalado).")
    cmd = [lp]
    if impressora:
        cmd += ["-d", impressora]
    if copias and copias > 1:
        cmd += ["-n", str(copias)]
    cmd.append(str(pdf))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return ResultadoImpressao(False, f"lp falhou: {proc.stderr.strip()}")
    alvo = impressora or "impressora padrão"
    return ResultadoImpressao(True, f"Enviado para {alvo} via CUPS ({copias} cópia(s)).")


# --------------------------------------------------------------------------- #
#  Dispatcher
# --------------------------------------------------------------------------- #
def imprimir(
    pdf_path: str | os.PathLike[str],
    impressora: str = "",
    copias: int = 1,
    sumatra_path: str | None = None,
    dry_run: bool = False,
) -> ResultadoImpressao:
    pdf = Path(pdf_path)
    if not pdf.is_file():
        return ResultadoImpressao(False, f"PDF não encontrado: {pdf}")
    if dry_run:
        alvo = impressora or "impressora padrão"
        return ResultadoImpressao(True, f"[dry-run] Imprimiria {pdf.name} em '{alvo}' ({copias} cópia(s)).")

    sistema = platform.system()
    if sistema == "Windows":
        return _imprimir_windows(pdf, impressora, copias, sumatra_path)
    # Linux, Darwin (macOS) e outros usam CUPS.
    return _imprimir_cups(pdf, impressora, copias)
