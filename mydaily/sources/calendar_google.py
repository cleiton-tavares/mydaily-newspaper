"""Integração com o Google Calendar para puxar a agenda do dia.

Dois métodos:
  - "ics": lê a URL secreta iCal do Google Calendar (simples, sem OAuth).
  - "api": usa a Google Calendar API com OAuth (mais robusto).

Ambos devolvem uma lista de dicts no mesmo formato da agenda do config:
    {"hora": "09:00", "titulo": "...", "detalhe": "...", "tipo": "TRABALHO"}
As dependências de cada método são importadas sob demanda, para não pesar
na instalação de quem não usa o Google Calendar.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

log = logging.getLogger(__name__)

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OMatinal/1.0"


def _classificar(titulo: str, local: str, descricao: str, dia_todo: bool) -> str:
    """Deriva um rótulo (tipo) para o compromisso."""
    if dia_todo:
        return "DIA TODO"
    texto = f"{local} {descricao}".lower()
    if any(p in texto for p in ("meet.google.com", "zoom.us", "teams.microsoft", "hangout")):
        return "ONLINE"
    return ""


def _fmt_detalhe(local: str, fim: datetime | None, tz: ZoneInfo) -> str:
    partes = []
    if fim is not None:
        partes.append(f"até {fim.astimezone(tz):%H:%M}")
    if local:
        # tira URLs longas do detalhe
        local_curto = local if len(local) <= 40 and "http" not in local.lower() else ""
        if local_curto:
            partes.append(local_curto)
    return " · ".join(partes)


# --------------------------------------------------------------------------- #
#  Método ICS (URL secreta iCal)
# --------------------------------------------------------------------------- #
def _agenda_ics(ics_url: str, tz: ZoneInfo, hoje: date, max_eventos: int) -> list[dict]:
    import requests
    import icalendar
    import recurring_ical_events

    resp = requests.get(ics_url, headers={"User-Agent": _UA}, timeout=25)
    resp.raise_for_status()
    cal = icalendar.Calendar.from_ical(resp.content)

    inicio = datetime.combine(hoje, time.min, tzinfo=tz)
    fim = datetime.combine(hoje, time.max, tzinfo=tz)
    eventos = recurring_ical_events.of(cal).between(inicio, fim)

    itens: list[dict] = []
    for ev in eventos:
        dtstart = ev.get("DTSTART").dt if ev.get("DTSTART") else None
        if dtstart is None:
            continue
        dtend_comp = ev.get("DTEND")
        dtend = dtend_comp.dt if dtend_comp else None

        dia_todo = not isinstance(dtstart, datetime)
        if dia_todo:
            hora = "dia"
        else:
            if dtstart.tzinfo is None:
                dtstart = dtstart.replace(tzinfo=tz)
            hora = f"{dtstart.astimezone(tz):%H:%M}"

        titulo = str(ev.get("SUMMARY", "")).strip() or "(sem título)"
        local = str(ev.get("LOCATION", "")).strip()
        descricao = str(ev.get("DESCRIPTION", "")).strip()
        fim_dt = dtend if isinstance(dtend, datetime) else None
        if fim_dt is not None and fim_dt.tzinfo is None:
            fim_dt = fim_dt.replace(tzinfo=tz)

        itens.append(
            {
                "_sort": (0 if dia_todo else 1, dtstart if isinstance(dtstart, datetime) else inicio),
                "hora": hora,
                "titulo": titulo,
                "detalhe": _fmt_detalhe(local, fim_dt, tz),
                "tipo": _classificar(titulo, local, descricao, dia_todo),
            }
        )

    itens.sort(key=lambda x: x["_sort"])
    for x in itens:
        x.pop("_sort", None)
    return itens[:max_eventos]


# --------------------------------------------------------------------------- #
#  Método API (OAuth)
# --------------------------------------------------------------------------- #
_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def _credenciais_api(credentials_file: str, token_file: str):
    from pathlib import Path

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    tok = Path(token_file)
    if tok.exists():
        creds = Credentials.from_authorized_user_file(str(tok), _SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(credentials_file).exists():
                raise FileNotFoundError(
                    f"Arquivo de credenciais OAuth não encontrado: {credentials_file}. "
                    "Baixe do Google Cloud Console (OAuth client, tipo Desktop)."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, _SCOPES)
            # Abre o navegador para autorizar (necessário só na 1ª vez).
            creds = flow.run_local_server(port=0)
        tok.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _agenda_api(
    credentials_file: str,
    token_file: str,
    calendar_id: str,
    tz: ZoneInfo,
    hoje: date,
    max_eventos: int,
) -> list[dict]:
    from googleapiclient.discovery import build

    creds = _credenciais_api(credentials_file, token_file)
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)

    inicio = datetime.combine(hoje, time.min, tzinfo=tz)
    fim = datetime.combine(hoje, time.max, tzinfo=tz)
    resp = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=inicio.isoformat(),
            timeMax=fim.isoformat(),
            singleEvents=True,          # expande eventos recorrentes
            orderBy="startTime",
            timeZone=str(tz),
        )
        .execute()
    )

    itens: list[dict] = []
    for ev in resp.get("items", []):
        start = ev.get("start", {})
        end = ev.get("end", {})
        dia_todo = "date" in start and "dateTime" not in start
        if dia_todo:
            hora = "dia"
        else:
            dt = datetime.fromisoformat(start["dateTime"]).astimezone(tz)
            hora = f"{dt:%H:%M}"
        fim_dt = None
        if "dateTime" in end:
            fim_dt = datetime.fromisoformat(end["dateTime"]).astimezone(tz)

        titulo = (ev.get("summary") or "(sem título)").strip()
        local = (ev.get("location") or "").strip()
        descricao = (ev.get("description") or "").strip()
        online = bool(ev.get("hangoutLink")) or bool(ev.get("conferenceData"))
        tipo = "DIA TODO" if dia_todo else ("ONLINE" if online else _classificar(titulo, local, descricao, False))

        itens.append(
            {
                "hora": hora,
                "titulo": titulo,
                "detalhe": _fmt_detalhe(local, fim_dt, tz),
                "tipo": tipo,
            }
        )
    return itens[:max_eventos]


# --------------------------------------------------------------------------- #
#  Entrada única
# --------------------------------------------------------------------------- #
def obter_agenda(
    metodo: str,
    tz: ZoneInfo,
    hoje: date,
    *,
    ics_url: str = "",
    credentials_file: str = "credentials.json",
    token_file: str = "token.json",
    calendar_id: str = "primary",
    max_eventos: int = 6,
) -> list[dict]:
    """Puxa a agenda do dia do Google Calendar. Lança exceção em caso de falha
    (o chamador decide o fallback)."""
    metodo = (metodo or "ics").lower()
    if metodo == "ics":
        if not ics_url:
            raise ValueError("google_calendar.ics_url (ou GOOGLE_ICS_URL) não configurado.")
        return _agenda_ics(ics_url, tz, hoje, max_eventos)
    if metodo == "api":
        return _agenda_api(credentials_file, token_file, calendar_id, tz, hoje, max_eventos)
    raise ValueError(f"Método de agenda desconhecido: {metodo!r} (use 'ics' ou 'api').")
