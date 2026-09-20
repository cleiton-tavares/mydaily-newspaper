"""Carregamento de configuração (config.yaml) e segredos (.env)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class LLMSettings:
    base_url: str
    api_key: str
    model: str
    temperature: float = 0.5
    max_itens_por_categoria: int = 14
    chromium_path: str | None = None


@dataclass
class Config:
    """Configuração completa já resolvida (config.yaml + .env)."""

    raw: dict[str, Any]
    llm: LLMSettings
    path: Path

    # ---- atalhos de acesso ----
    def section(self, name: str, default: Any = None) -> Any:
        return self.raw.get(name, default if default is not None else {})

    @property
    def jornal(self) -> dict[str, Any]:
        return self.raw.get("jornal", {})

    @property
    def clima(self) -> dict[str, Any]:
        return self.raw.get("clima", {})

    @property
    def feeds(self) -> dict[str, list[dict[str, str]]]:
        return self.raw.get("feeds", {})

    @property
    def numeros(self) -> list[dict[str, Any]]:
        return self.raw.get("numeros", [])

    @property
    def agenda(self) -> list[dict[str, Any]]:
        return self.raw.get("agenda", [])

    @property
    def lembretes(self) -> list[str]:
        return self.raw.get("lembretes", [])

    @property
    def impressao(self) -> dict[str, Any]:
        return self.raw.get("impressao", {})

    @property
    def tz(self) -> ZoneInfo:
        nome = self.jornal.get("fuso", "America/Sao_Paulo")
        try:
            return ZoneInfo(nome)
        except Exception:
            return ZoneInfo("America/Sao_Paulo")

    @property
    def output_dir(self) -> Path:
        rel = self.raw.get("saida", {}).get("diretorio", "output")
        p = Path(rel)
        if not p.is_absolute():
            p = REPO_ROOT / p
        p.mkdir(parents=True, exist_ok=True)
        return p

    def numero_edicao(self, hoje: date) -> int:
        """Edição = dias desde `edicao_inicio` + `edicao_offset`."""
        inicio_raw = self.jornal.get("edicao_inicio")
        offset = int(self.jornal.get("edicao_offset", 1))
        if not inicio_raw:
            return offset
        try:
            inicio = date.fromisoformat(str(inicio_raw))
        except ValueError:
            return offset
        return (hoje - inicio).days + offset


def _resolve_config_path(explicit: str | os.PathLike[str] | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env_path = os.getenv("MYDAILY_CONFIG")
    if env_path:
        return Path(env_path).expanduser().resolve()
    candidate = REPO_ROOT / "config.yaml"
    if candidate.exists():
        return candidate
    # fallback: exemplo (permite rodar sem copiar, com dados de placeholder)
    return REPO_ROOT / "config.example.yaml"


def load_config(path: str | os.PathLike[str] | None = None) -> Config:
    """Lê .env + config.yaml e devolve um objeto Config validado."""
    load_dotenv(REPO_ROOT / ".env")

    cfg_path = _resolve_config_path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(
            f"Arquivo de configuração não encontrado: {cfg_path}. "
            "Copie config.example.yaml para config.yaml."
        )
    with cfg_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    llm_cfg = raw.get("llm", {}) or {}
    base_url = os.getenv("LITELLM_BASE_URL", "").strip()
    api_key = os.getenv("LITELLM_API_KEY", "").strip()
    model = (llm_cfg.get("modelo") or os.getenv("LITELLM_MODEL", "")).strip()

    llm = LLMSettings(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=float(llm_cfg.get("temperatura", 0.5)),
        max_itens_por_categoria=int(llm_cfg.get("max_itens_por_categoria", 14)),
        chromium_path=os.getenv("PLAYWRIGHT_CHROMIUM_PATH", "").strip() or None,
    )

    return Config(raw=raw, llm=llm, path=cfg_path)


def require_llm_credentials(cfg: Config) -> list[str]:
    """Devolve a lista de variáveis faltando (vazia se está tudo ok)."""
    faltando: list[str] = []
    if not cfg.llm.base_url:
        faltando.append("LITELLM_BASE_URL")
    if not cfg.llm.api_key:
        faltando.append("LITELLM_API_KEY")
    if not cfg.llm.model:
        faltando.append("LITELLM_MODEL (ou llm.modelo no config.yaml)")
    return faltando
