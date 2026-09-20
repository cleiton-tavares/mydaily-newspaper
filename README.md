# O Matinal — jornal matinal automático

Monta, todas as manhãs, um jornal de **duas páginas A4** com as principais
notícias do **mundo**, do **Brasil** e de **inteligência artificial**, além de
**clima**, **indicadores do dia**, **agenda** e **lembretes**. O conteúdo é
coletado da internet (feeds RSS + APIs públicas), escrito por uma **LLM através
do seu proxy LiteLLM**, renderizado no layout do jornal e **enviado para a sua
impressora**.

![layout](https://img.shields.io/badge/formato-A4%20·%202%20p%C3%A1ginas-111)

---

## Como funciona

```
RSS (mundo/brasil/IA) ─┐
Clima (Open-Meteo)     ├─▶ LiteLLM escreve o editorial ─▶ HTML (templates)
Indicadores (APIs)     ┘                                        │
Agenda/Lembretes (config) ──────────────────────────────────────┤
                                                                 ▼
                                              PDF A4 (Chromium) ─▶ impressora
```

1. **Coleta** — lê os feeds RSS configurados, o clima real (Open-Meteo, sem
   chave) e os indicadores do dia (dólar, Ibovespa, Selic, bitcoin, IPCA).
2. **Redação** — envia as manchetes reais para a sua LLM (via LiteLLM) que
   seleciona o que é relevante e escreve as chamadas e as reportagens.
3. **Diagramação** — preenche os dois templates HTML fiéis ao layout.
4. **Impressão** — gera o PDF A4 com o Chromium e manda para a impressora.

> Clima, indicadores, agenda e lembretes entram com **dados reais/seus** — a LLM
> não inventa esses números. Ela cuida só do texto jornalístico, sempre baseada
> nas notícias coletadas.

---

## Instalação

Requer **Python 3.10+**.

```bash
# 1. Dependências
pip install -r requirements.txt

# 2. Navegador headless usado para gerar o PDF (uma vez só)
playwright install chromium

# 3. Configuração
cp .env.example .env                 # credenciais do LiteLLM
cp config.example.yaml config.yaml   # feeds, clima, agenda, impressora...
```

Edite o `.env` com os dados do seu proxy LiteLLM:

```dotenv
LITELLM_BASE_URL=http://localhost:4000
LITELLM_API_KEY=sk-sua-chave
LITELLM_MODEL=gpt-4o
```

> O LiteLLM expõe uma API compatível com a OpenAI. A `LITELLM_BASE_URL` é a URL
> do seu proxy (com ou sem `/v1` no final — os dois funcionam).

---

## Uso

```bash
# Pré-visualizar o layout sem internet nem LLM (conteúdo de exemplo):
python -m mydaily --demo --no-print

# Gerar o jornal de verdade e imprimir:
python -m mydaily

# Gerar sem imprimir (só o PDF em output/):
python -m mydaily --no-print

# Simular a impressão (não envia à impressora):
python -m mydaily --dry-run-print
```

Saídas ficam em `output/o-matinal-AAAA-MM-DD.html` e `.pdf`.

### Opções

| Opção | Descrição |
|---|---|
| `--demo` | Usa conteúdo de exemplo (sem internet/LLM) para conferir o layout |
| `--no-print` | Gera o PDF mas não imprime |
| `--no-pdf` | Gera apenas o HTML |
| `--dry-run-print` | Simula a impressão |
| `--printer "Nome"` | Sobrescreve a impressora do config |
| `--date AAAA-MM-DD` | Força a data do jornal |
| `--config caminho` | Usa outro arquivo de config |
| `-v` | Log detalhado |

---

## Impressão no Windows

Por padrão o app procura o **SumatraPDF** (impressão silenciosa, sem abrir
janela) nos locais comuns de instalação. É a forma recomendada:

1. Instale o [SumatraPDF](https://www.sumatrapdfreader.org/).
2. No `config.yaml`, em `impressao`, informe o nome da impressora
   (deixe vazio para usar a padrão) e, se necessário, o `sumatra_path`.

Sem o SumatraPDF, o app cai no `Start-Process -Verb Print` do PowerShell, que
usa o visualizador de PDF padrão do Windows (pode abrir uma janela).

> Em Linux/macOS a impressão usa o `lp` (CUPS) automaticamente.

---

## Rodar toda manhã automaticamente (Windows)

Use o **Agendador de Tarefas** (Task Scheduler):

1. Crie uma tarefa básica → disparador **Diariamente**, ex.: 05:30.
2. Ação: **Iniciar um programa**
   - Programa: `python`
   - Argumentos: `-m mydaily`
   - Iniciar em: a pasta deste projeto (ex.: `C:\Users\voce\mydaily-newspaper`)
3. Marque "Executar estando o usuário conectado ou não".

Ou, via PowerShell (ajuste os caminhos):

```powershell
$acao   = New-ScheduledTaskAction -Execute "python" -Argument "-m mydaily" -WorkingDirectory "C:\caminho\mydaily-newspaper"
$gatilho = New-ScheduledTaskTrigger -Daily -At 5:30am
Register-ScheduledTask -TaskName "O Matinal" -Action $acao -Trigger $gatilho -Description "Jornal matinal"
```

---

## Configuração (`config.yaml`)

- **`jornal`** — título, tagline, local, fuso, número da edição.
- **`clima`** — cidade + latitude/longitude (Open-Meteo). Padrão: Maceió.
- **`feeds`** — feeds RSS por categoria (`mundo`, `brasil`, `ia`). Adicione/remova
  à vontade; dá para usar buscas do Google Notícias por tema.
- **`numeros`** — indicadores do dia. Cada um tem um `provider`
  (`awesomeapi`, `bcb_sgs`, `yahoo`, `static`) e um `fallback` usado se a fonte
  online falhar, para o jornal nunca sair quebrado.
- **`agenda`** / **`lembretes`** — seções pessoais da barra lateral.
- **`impressao`** — impressora, cópias e caminho do SumatraPDF.

---

## Estrutura do projeto

```
mydaily/
├── cli.py            # linha de comando + orquestração do pipeline
├── config.py         # leitura de config.yaml + .env
├── models.py         # estruturas de dados
├── llm.py            # cliente LiteLLM + geração do editorial (JSON)
├── render.py         # contexto + renderização Jinja2
├── pdf.py            # HTML -> PDF (Playwright/Chromium)
├── printing.py       # impressão (Windows / CUPS)
├── sample.py         # conteúdo de exemplo (modo --demo)
├── sources/
│   ├── rss.py        # coleta de notícias
│   ├── weather.py    # clima (Open-Meteo)
│   └── markets.py    # indicadores (AwesomeAPI, BCB, Yahoo)
└── templates/
    ├── newspaper.html.j2   # documento (as duas folhas)
    ├── page1.html.j2       # capa
    ├── page2.html.j2       # reportagens
    └── icons.html.j2       # ícones SVG
```

---

## Solução de problemas

- **PDF em branco ou sem estilo** — o layout usa Tailwind e Google Fonts via CDN;
  é preciso ter internet no momento de gerar o PDF.
- **`Executable doesn't exist` (Playwright)** — rode `playwright install chromium`.
  Em ambientes com o Chromium em outro lugar, aponte `PLAYWRIGHT_CHROMIUM_PATH`.
- **`Faltam credenciais do LiteLLM`** — preencha o `.env` ou use `--demo`.
- **Indicador saindo com o valor de `fallback`** — a fonte online falhou (ex.:
  limite de requisições); o valor do `config.yaml` foi usado no lugar.
