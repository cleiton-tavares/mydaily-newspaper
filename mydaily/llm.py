"""Geração do conteúdo editorial via LLM (proxy LiteLLM, API OpenAI-compatível)."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import OpenAI

from .config import Config
from .models import NewsItem

log = logging.getLogger(__name__)


SYSTEM_PROMPT = """\
Você é o editor-chefe do "O Matinal", um jornal matinal brasileiro conciso e
elegante. Você recebe manchetes e resumos REAIS coletados de feeds RSS hoje de
manhã e precisa transformá-los em um jornal de duas páginas.

Regras invioláveis:
- Escreva em português do Brasil, com estilo jornalístico limpo, direto e sóbrio.
- Baseie-se SOMENTE nas notícias fornecidas. Não invente fatos, números,
  nomes ou declarações que não estejam no material. Se faltar detalhe, escreva
  de forma mais geral em vez de inventar.
- Nas reportagens longas da página 2, você pode desenvolver contexto e análise,
  mas sem criar fatos novos: apenas organize e explique o que veio no material.
- Cite as fontes reais (o campo "fonte" de cada item) nos campos de crédito.
- As aspas/citações da página 2 devem ser plausíveis e atribuídas a pessoas que
  apareçam no material; se não houver ninguém citável, use uma frase-síntese sem
  atribuir a uma pessoa específica (ex.: autor "Análise · O Matinal").
- Não use markdown, emojis ou aspas tipográficas desnecessárias.
- Responda ESTRITAMENTE com um único objeto JSON válido, sem texto ao redor.
"""

# Esqueleto do JSON esperado (também serve de documentação para o modelo).
SCHEMA_HINT = """\
Formato EXATO do JSON de resposta:

{
  "briefing": {
    "mundo": "uma linha (máx. ~60 caracteres) resumindo o principal do mundo",
    "brasil": "uma linha resumindo o principal do Brasil",
    "ia": "uma linha resumindo o principal de IA"
  },
  "page1": {
    "mundo": {
      "lead":   {"headline": "manchete principal do mundo (1 frase)",
                 "body": "2 a 3 frases de resumo", "meta": "FONTE1 · FONTE2"},
      "secondary": [
        {"headline": "manchete secundária", "body": "1 a 2 frases", "meta": "FONTE"},
        {"headline": "manchete secundária", "body": "1 a 2 frases", "meta": "FONTE"}
      ]
    },
    "brasil": {"stories": [
        {"headline": "...", "body": "1 a 2 frases", "meta": "FONTE"},
        {"headline": "...", "body": "1 a 2 frases", "meta": "FONTE"},
        {"headline": "...", "body": "1 a 2 frases", "meta": "FONTE"},
        {"headline": "...", "body": "1 a 2 frases", "meta": "FONTE"}
    ]},
    "ia": {"stories": [
        {"headline": "...", "body": "1 a 2 frases", "meta": "FONTE"},
        {"headline": "...", "body": "1 a 2 frases", "meta": "FONTE"},
        {"headline": "...", "body": "1 a 2 frases", "meta": "FONTE"},
        {"headline": "...", "body": "1 a 2 frases", "meta": "FONTE"}
    ]}
  },
  "page2": {
    "featured": {
      "kicker": "MUNDO · TEMA EM CAIXA ALTA",
      "source": "DE LOCAL · FONTES",
      "headline": "manchete longa e envolvente da reportagem principal",
      "standfirst": "linha fina em itálico, 1 a 2 frases",
      "paragraphs": ["parágrafo 1", "parágrafo 2", "parágrafo 3", "parágrafo 4", "parágrafo 5"],
      "quote": {"text": "citação de destaque", "author": "NOME, CARGO"}
    },
    "secondary": [
      {
        "kicker": "BRASIL · ECONOMIA",
        "source": "LOCAL · FONTES",
        "headline": "manchete da reportagem de Brasil/economia",
        "standfirst": "linha fina em itálico",
        "paragraphs": ["parágrafo 1", "parágrafo 2", "parágrafo 3"],
        "quote": {"text": "citação", "author": "NOME, CARGO"}
      },
      {
        "kicker": "INTELIGÊNCIA ARTIFICIAL · TEMA",
        "source": "LOCAL · FONTES",
        "headline": "manchete da reportagem de IA",
        "standfirst": "linha fina em itálico",
        "paragraphs": ["parágrafo 1", "parágrafo 2", "parágrafo 3"],
        "quote": {"text": "citação", "author": "NOME, CARGO"}
      }
    ],
    "brief_notes": [
      {"label": "MUNDO",   "title": "título curto", "body": "2 frases"},
      {"label": "BRASIL",  "title": "título curto", "body": "2 frases"},
      {"label": "IA",      "title": "título curto", "body": "2 frases"},
      {"label": "CIÊNCIA", "title": "título curto", "body": "2 frases"}
    ]
  },
  "reading": {
    "title": "sugestão de leitura para o café (um tema aprofundado do dia)",
    "body": "3 a 4 frases explicando por que vale a leitura",
    "source": "FONTE",
    "minutes": 6
  }
}
"""


def _itens_para_texto(noticias: dict[str, list[NewsItem]], limite: int) -> str:
    blocos: list[str] = []
    for categoria, itens in noticias.items():
        blocos.append(f"\n### CATEGORIA: {categoria.upper()}")
        if not itens:
            blocos.append("(sem itens coletados)")
            continue
        for i, item in enumerate(itens[:limite], 1):
            resumo = item.resumo[:280] if item.resumo else ""
            data = item.publicado.strftime("%d/%m %H:%M") if item.publicado else "s/ data"
            blocos.append(f"{i}. [{item.fonte} · {data}] {item.titulo}\n   {resumo}")
    return "\n".join(blocos)


def _client(cfg: Config) -> OpenAI:
    base = cfg.llm.base_url.rstrip("/")
    # A API do LiteLLM é compatível com a OpenAI em <base>/v1 ou <base>.
    # O SDK acrescenta /chat/completions ao base_url informado.
    return OpenAI(base_url=base, api_key=cfg.llm.api_key)


def _extrair_json(texto: str) -> dict[str, Any]:
    """Extrai o primeiro objeto JSON de uma string (tolera cercas de código)."""
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```[a-zA-Z]*\n?", "", texto)
        texto = re.sub(r"\n?```$", "", texto).strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        inicio = texto.find("{")
        fim = texto.rfind("}")
        if inicio != -1 and fim != -1 and fim > inicio:
            return json.loads(texto[inicio : fim + 1])
        raise


def gerar_editorial(cfg: Config, noticias: dict[str, list[NewsItem]], data_str: str) -> dict[str, Any]:
    """Chama a LLM e devolve o dicionário editorial normalizado."""
    client = _client(cfg)
    material = _itens_para_texto(noticias, cfg.llm.max_itens_por_categoria)

    user_prompt = (
        f"Data de hoje: {data_str}.\n"
        f"Local do jornal: {cfg.jornal.get('local', '')}.\n\n"
        "A seguir estão as notícias reais coletadas hoje de manhã, agrupadas por "
        "categoria. Selecione as mais relevantes e escreva o jornal.\n"
        f"{material}\n\n"
        "Monte agora o jornal seguindo exatamente o formato pedido.\n\n"
        f"{SCHEMA_HINT}"
    )

    kwargs: dict[str, Any] = {
        "model": cfg.llm.model,
        "temperature": cfg.llm.temperature,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }
    # Tenta o modo JSON; se o modelo/rota não suportar, refaz sem ele.
    try:
        resp = client.chat.completions.create(response_format={"type": "json_object"}, **kwargs)
    except Exception as exc:  # noqa: BLE001
        log.info("response_format json_object não aceito (%s); repetindo sem ele.", exc)
        resp = client.chat.completions.create(**kwargs)

    conteudo = resp.choices[0].message.content or ""
    dados = _extrair_json(conteudo)
    return normalizar(dados)


# --------------------------------------------------------------------------- #
#  Normalização: garante que todas as chaves existam com o tipo certo,
#  para os templates nunca quebrarem por falta de campo.
# --------------------------------------------------------------------------- #
def _story(d: Any) -> dict[str, str]:
    d = d if isinstance(d, dict) else {}
    return {
        "headline": str(d.get("headline", "")).strip(),
        "body": str(d.get("body", "")).strip(),
        "meta": str(d.get("meta", "")).strip(),
    }


def _lista_stories(lst: Any, n: int) -> list[dict[str, str]]:
    lst = lst if isinstance(lst, list) else []
    out = [_story(x) for x in lst[:n]]
    while len(out) < n:
        out.append({"headline": "", "body": "", "meta": ""})
    return out


def _quote(d: Any) -> dict[str, str]:
    d = d if isinstance(d, dict) else {}
    return {"text": str(d.get("text", "")).strip(), "author": str(d.get("author", "")).strip()}


def _reportagem(d: Any, n_paragrafos: int) -> dict[str, Any]:
    d = d if isinstance(d, dict) else {}
    paras = d.get("paragraphs")
    paras = [str(p).strip() for p in paras if str(p).strip()] if isinstance(paras, list) else []
    if not paras:
        paras = [""]
    return {
        "kicker": str(d.get("kicker", "")).strip(),
        "source": str(d.get("source", "")).strip(),
        "headline": str(d.get("headline", "")).strip(),
        "standfirst": str(d.get("standfirst", "")).strip(),
        "paragraphs": paras,
        "quote": _quote(d.get("quote")),
    }


def normalizar(d: dict[str, Any]) -> dict[str, Any]:
    d = d if isinstance(d, dict) else {}
    brief = d.get("briefing", {}) if isinstance(d.get("briefing"), dict) else {}
    p1 = d.get("page1", {}) if isinstance(d.get("page1"), dict) else {}
    p2 = d.get("page2", {}) if isinstance(d.get("page2"), dict) else {}
    mundo = p1.get("mundo", {}) if isinstance(p1.get("mundo"), dict) else {}

    notes = p2.get("brief_notes")
    notes = notes if isinstance(notes, list) else []
    labels_default = ["MUNDO", "BRASIL", "IA", "CIÊNCIA"]
    brief_notes = []
    for i in range(4):
        nd = notes[i] if i < len(notes) and isinstance(notes[i], dict) else {}
        brief_notes.append(
            {
                "label": str(nd.get("label", labels_default[i])).strip() or labels_default[i],
                "title": str(nd.get("title", "")).strip(),
                "body": str(nd.get("body", "")).strip(),
            }
        )

    secundarias = p2.get("secondary")
    secundarias = secundarias if isinstance(secundarias, list) else []
    sec_out = [_reportagem(secundarias[i] if i < len(secundarias) else {}, 3) for i in range(2)]

    reading = d.get("reading", {}) if isinstance(d.get("reading"), dict) else {}

    return {
        "briefing": {
            "mundo": str(brief.get("mundo", "")).strip(),
            "brasil": str(brief.get("brasil", "")).strip(),
            "ia": str(brief.get("ia", "")).strip(),
        },
        "page1": {
            "mundo": {
                "lead": _story(mundo.get("lead")),
                "secondary": _lista_stories(mundo.get("secondary"), 2),
            },
            "brasil": {"stories": _lista_stories((p1.get("brasil") or {}).get("stories"), 4)},
            "ia": {"stories": _lista_stories((p1.get("ia") or {}).get("stories"), 4)},
        },
        "page2": {
            "featured": _reportagem(p2.get("featured"), 5),
            "secondary": sec_out,
            "brief_notes": brief_notes,
        },
        "reading": {
            "title": str(reading.get("title", "")).strip(),
            "body": str(reading.get("body", "")).strip(),
            "source": str(reading.get("source", "")).strip(),
            "minutes": reading.get("minutes", 6),
        },
    }
