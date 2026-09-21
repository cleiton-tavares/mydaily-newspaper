# O Matinal — jornal matinal automático

Monta, todas as manhãs, um jornal de **até três páginas A4**:

- **Página 1** — capa: mundo, Brasil, IA, **clima**, **indicadores do dia**,
  **agenda** e **lembretes**.
- **Página 2** — reportagens longas de mundo, Brasil e IA + "em poucas linhas".
- **Página 3** (opcional) — cadernos de **E-sports** e **Cultura**,
  **quadrinho do dia** e **lançamentos da semana** (jogos, cinema, música, livros).

O conteúdo é coletado da internet (feeds RSS + APIs públicas), escrito por uma
**LLM através do seu proxy LiteLLM**, renderizado no layout do jornal e
**enviado para a sua impressora**.

![layout](https://img.shields.io/badge/formato-A4%20·%20at%C3%A9%203%20p%C3%A1ginas-111)

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

## Puxar a agenda do Google Calendar

Por padrão a agenda vem da lista `agenda:` no `config.yaml`. Para puxar os
compromissos reais do dia do Google Calendar, escolha um dos dois métodos abaixo
(cada um instala só o que precisa). Se a consulta falhar (sem internet, URL
errada), o app volta automaticamente para a lista `agenda:` do config — o jornal
nunca sai sem agenda.

### Método 1 — ICS (mais simples, recomendado)

Usa o "endereço secreto" do seu calendário. Sem Google Cloud, sem OAuth. Precisa
só de duas bibliotecas leves:

```bash
pip install icalendar recurring_ical_events
```

1. Abra o [Google Calendar](https://calendar.google.com) no computador.
2. Passe o mouse sobre o calendário desejado (coluna esquerda) → ⋮ →
   **Configurações e compartilhamento**.
3. Role até **Integrar agenda** → copie o **Endereço secreto no formato iCal**.
4. Cole no `.env` (é um segredo — quem tiver a URL vê sua agenda):

   ```dotenv
   GOOGLE_ICS_URL=https://calendar.google.com/calendar/ical/.../basic.ics
   ```

5. No `config.yaml`, ative:

   ```yaml
   google_calendar:
     ativar: true
     metodo: "ics"
   ```

Pronto. Eventos recorrentes e de dia inteiro são tratados automaticamente. Teste
com `python -m mydaily --no-print -v` e confira a linha `Agenda: Google Calendar`.

> Dica: se preferir, dá para colar a URL em `google_calendar.ics_url` no
> `config.yaml`, mas o `.env` é o lugar mais seguro para segredos.

### Método 2 — API oficial (OAuth)

Mais robusto (não depende de URL secreta), mas exige um projeto no Google Cloud.
Instale as dependências da API:

```bash
pip install -r requirements-google.txt
```

1. No [Google Cloud Console](https://console.cloud.google.com/): crie um projeto
   e **ative a Google Calendar API**.
2. Em **Credenciais** → **Criar credenciais** → **ID do cliente OAuth** → tipo
   **App para computador**. Baixe o JSON e salve como `credentials.json` na raiz
   do projeto.
3. Em **Tela de consentimento OAuth**, adicione seu e-mail como usuário de teste.
4. No `config.yaml`, use `metodo: "api"`.
5. Na **primeira execução**, o app abre o navegador para você autorizar; depois
   disso ele grava um `token.json` e passa a renovar o acesso sozinho.

   ```bash
   python -m mydaily --no-print   # autoriza na 1ª vez
   ```

> `credentials.json` e `token.json` já estão no `.gitignore`. Rode a primeira
> autorização manualmente antes de agendar a tarefa automática das manhãs.

---

## Página 3 — cadernos (E-sports, Cultura, Quadrinhos, Lançamentos)

A terceira página é opcional. No `config.yaml`:

```yaml
cadernos:
  ativar: true      # false = jornal de 2 páginas
```

- **E-sports** e **Cultura** são escritos pela LLM a partir de feeds RSS próprios
  (categorias `esports` e `cultura`, editáveis em `feeds:`), com tabelas de
  resultados/jogos e a agenda "O que fazer hoje em Maceió".
- **Lançamentos da semana** são quatro resenhas curtas (jogo, cinema, música,
  livro) com nota em estrelas, curadas pela LLM.
- **Quadrinho do dia** é buscado da fonte do autor:

```yaml
quadrinhos:
  ativar: true
  feed_url: "https://www.willtirando.com.br/feed/"
  site_url: "https://www.willtirando.com.br/"
  autor: "Will Tirando"
```

> **Sobre o quadrinho:** o app baixa a tira **publicada pelo autor** e a embute
> no seu jornal, sempre creditando a fonte — ele não redesenha nem altera a arte.
> Use para leitura **pessoal** e respeite o direito autoral do autor; para
> distribuir o jornal, peça autorização. Se o download falhar, a página 3 sai
> sem a tira. Para trocar de quadrinho, aponte `feed_url`/`site_url` para outra
> fonte (qualquer site WordPress com RSS costuma funcionar).

Como E-sports/Cultura/Lançamentos e a agenda local dependem de feeds e do texto
da LLM, revise-os de vez em quando: são as seções mais "editoriais" do jornal.

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
│   ├── rss.py             # coleta de notícias
│   ├── weather.py         # clima (Open-Meteo)
│   ├── markets.py         # indicadores (AwesomeAPI, BCB, Yahoo)
│   ├── calendar_google.py # agenda do Google Calendar (ICS ou API)
│   └── comic.py           # tira do dia (página 3)
└── templates/
    ├── newspaper.html.j2   # documento (as três folhas)
    ├── page1.html.j2       # capa
    ├── page2.html.j2       # reportagens
    ├── page3.html.j2       # cadernos (e-sports, cultura, quadrinhos, lançamentos)
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
