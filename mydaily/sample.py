"""Dados de exemplo para pré-visualizar o layout sem internet/LLM (modo --demo)."""
from __future__ import annotations

from .models import HourForecast, MarketNumber, Weather


def editorial_exemplo() -> dict:
    return {
        "briefing": {
            "mundo": "Cúpula do clima chega ao dia decisivo em Nairóbi",
            "brasil": "Copom mantém Selic e sinaliza ciclo de cortes",
            "ia": "Novo modelo aberto supera benchmarks de raciocínio",
        },
        "page1": {
            "mundo": {
                "lead": {
                    "headline": "Cúpula do clima entra no dia decisivo com impasse sobre financiamento a países em desenvolvimento",
                    "body": "Negociadores em Nairóbi tentam fechar um acordo sobre o fundo de adaptação antes do encerramento. Delegações europeias sinalizam concessões, enquanto blocos do Sul Global exigem metas vinculantes. O texto final deve ser votado ainda hoje.",
                    "meta": "REUTERS · AFP",
                },
                "secondary": [
                    {
                        "headline": "Banco Central Europeu mantém juros e vê inflação convergindo à meta",
                        "body": "Decisão era esperada pelo mercado; presidente do BCE fala em cautela vigilante até dezembro.",
                        "meta": "FINANCIAL TIMES",
                    },
                    {
                        "headline": "Eleições no Chile: segundo turno terá disputa apertada, apontam pesquisas",
                        "body": "Diferença entre os candidatos está dentro da margem de erro a duas semanas do pleito.",
                        "meta": "EL PAÍS",
                    },
                ],
            },
            "brasil": {
                "stories": [
                    {
                        "headline": "Copom mantém Selic em 12,25% e abre porta para cortes a partir de novembro",
                        "body": "Comunicado destaca desinflação de serviços e ancoragem das expectativas. Mercado já precifica corte de 0,25 ponto.",
                        "meta": "VALOR · FOLHA",
                    },
                    {
                        "headline": "Nordeste lidera geração de empregos formais em agosto, diz Caged",
                        "body": "Alagoas registrou saldo positivo pelo sexto mês seguido, puxado por serviços e construção civil.",
                        "meta": "G1 · AGÊNCIA BRASIL",
                    },
                    {
                        "headline": "STF retoma julgamento sobre marco regulatório das plataformas digitais",
                        "body": "Sessão de hoje deve definir responsabilidade das redes por conteúdo de terceiros; placar está em 4 a 2.",
                        "meta": "O GLOBO · CONJUR",
                    },
                    {
                        "headline": "Governo anuncia leilão de transmissão com foco em energia eólica offshore",
                        "body": "Investimento previsto de R$ 18 bilhões; lotes no litoral de Alagoas e Rio Grande do Norte.",
                        "meta": "ESTADÃO",
                    },
                ]
            },
            "ia": {
                "stories": [
                    {
                        "headline": "Modelo de pesos abertos supera concorrentes fechados em raciocínio matemático",
                        "body": "Lançado ontem, o modelo de 70B parâmetros lidera três benchmarks e já está disponível para uso comercial.",
                        "meta": "ARXIV · HUGGING FACE",
                    },
                    {
                        "headline": "Agentes autônomos passam a operar 40% dos tickets de suporte em grandes varejistas",
                        "body": "Levantamento com 120 empresas mostra redução de 30% no tempo de resposta.",
                        "meta": "MIT TECH REVIEW",
                    },
                    {
                        "headline": "União Europeia publica guia final de conformidade do AI Act para sistemas de alto risco",
                        "body": "Prazo para adequação começa em fevereiro; multas podem chegar a 7% do faturamento global.",
                        "meta": "EURACTIV",
                    },
                    {
                        "headline": "Empresas de nuvem anunciam protocolo comum para interoperabilidade de agentes",
                        "body": "Especificação aberta permite que agentes de fornecedores diferentes troquem tarefas com segurança.",
                        "meta": "THE VERGE",
                    },
                ]
            },
        },
        "page2": {
            "featured": {
                "kicker": "MUNDO · CÚPULA DO CLIMA",
                "source": "DE NAIRÓBI · REUTERS, AFP E APURAÇÃO PRÓPRIA",
                "headline": "O dia em que o dinheiro decide o clima: por que o fundo de adaptação travou a cúpula de Nairóbi",
                "standfirst": "Países ricos oferecem 60 bilhões de dólares por ano; o Sul Global pede o dobro e quer que a promessa seja obrigatória. O texto final será votado hoje.",
                "paragraphs": [
                    "NAIRÓBI — Às três da madrugada de ontem, a delegação da União Europeia deixou a sala de negociação com uma proposta nova: 60 bilhões de dólares por ano, a partir de 2028, para ajudar países pobres a se proteger de secas, enchentes e do avanço do mar.",
                    "Não foi suficiente. Em menos de uma hora, o grupo dos 77 países em desenvolvimento respondeu que aceita discutir o valor, mas não a forma. O que eles querem é que o compromisso seja vinculante, com sanções para quem não pagar.",
                    "O impasse tem raízes antigas. Em 2009, em Copenhague, os países ricos prometeram 100 bilhões de dólares anuais até 2020. A meta só foi cumprida em 2022, e boa parte veio na forma de empréstimos, não de doações.",
                    "O Brasil, que ocupa a presidência do grupo latino-americano, tenta um meio-termo: um mecanismo de revisão a cada três anos, com metas crescentes e transparência pública sobre quem pagou o quê.",
                    "A votação do texto final está marcada para as 16h de hoje, horário de Nairóbi. Se não houver acordo, a cúpula pode ser estendida por um dia, como aconteceu em cinco das últimas sete edições.",
                ],
                "quote": {
                    "text": "Não estamos pedindo caridade. Estamos pedindo que a conta seja paga por quem sujou.",
                    "author": "MARIAM OUÉDRAOGO, NEGOCIADORA DE BURKINA FASO",
                },
            },
            "secondary": [
                {
                    "kicker": "BRASIL · ECONOMIA",
                    "source": "BRASÍLIA · VALOR E FOLHA",
                    "headline": "Selic parada, mas o Copom já fala em novembro: o que muda para quem tem dívida",
                    "standfirst": "Comitê manteve a taxa em 12,25% pela terceira vez, mas retirou do comunicado a expressão por período prolongado.",
                    "paragraphs": [
                        "BRASÍLIA — A decisão de ontem era a mais esperada do ano pelo mercado, não pelo que o Copom faria, mas pelo que diria. A Selic ficou em 12,25% ao ano, como todos previam. A mudança estava no texto.",
                        "O comunicado deixou de dizer que a taxa ficaria alta por período prolongado. Em linguagem de banco central, isso significa que a porta para cortes está aberta.",
                        "Para o consumidor, o efeito não é imediato. Um corte de 0,25 ponto em novembro reduz pouco a parcela no mês, mas é relevante ao longo do contrato.",
                    ],
                    "quote": {
                        "text": "O Copom não corta na largada. Ele avisa, espera o mercado digerir, e então age.",
                        "author": "MÔNICA DE BOLLE, ECONOMISTA",
                    },
                },
                {
                    "kicker": "INTELIGÊNCIA ARTIFICIAL · PESOS ABERTOS",
                    "source": "SÃO FRANCISCO · MIT TECHNOLOGY REVIEW E THE VERGE",
                    "headline": "O modelo aberto que venceu os fechados: como um laboratório pequeno chegou ao topo",
                    "standfirst": "Lançado ontem sob licença permissiva, o modelo de 70 bilhões de parâmetros lidera três benchmarks de matemática.",
                    "paragraphs": [
                        "SÃO FRANCISCO — O anúncio saiu às seis da manhã, em um post de doze linhas. Não havia evento nem executivo no palco. Havia um link para os pesos do modelo e uma tabela com resultados.",
                        "A receita, segundo o relatório, não foi mais dados nem mais chips, mas uma técnica de treinamento em duas etapas. O custo total, estimado em 9 milhões de dólares, é uma fração do gasto pelos concorrentes.",
                        "Há ressalvas. O modelo é forte em matemática e código, mas fica atrás em tarefas de linguagem longa e em português, onde os benchmarks mostram queda de desempenho.",
                    ],
                    "quote": {
                        "text": "A vantagem dos modelos fechados sempre foi de meses, nunca de anos. Agora é de semanas.",
                        "author": "ANDREJ KARPATHY, PESQUISADOR",
                    },
                },
            ],
            "brief_notes": [
                {"label": "MUNDO", "title": "Japão aprova pacote de 40 bilhões de dólares para semicondutores", "body": "O plano inclui subsídios para uma segunda fábrica da TSMC em Kumamoto. O texto passou com folga na Câmara Baixa."},
                {"label": "BRASIL", "title": "Maceió inicia obras do corredor de ônibus da Avenida Fernandes Lima", "body": "A primeira etapa deve ficar pronta em 14 meses, com faixa exclusiva, 22 estações e integração com o VLT."},
                {"label": "IA", "title": "Justiça alemã condena empresa por demissão decidida por algoritmo", "body": "Tribunal entendeu que a funcionária tinha direito a revisão humana. É a primeira decisão do tipo sob o AI Act."},
                {"label": "CIÊNCIA", "title": "Sonda Europa Clipper envia primeiras imagens da lua gelada de Júpiter", "body": "As fotos mostram rachaduras na crosta de gelo com até 3 km de largura. O sobrevoo principal está marcado para abril."},
            ],
        },
        "reading": {
            "title": "Por que o fundo de adaptação virou o centro da geopolítica do clima",
            "body": "Uma leitura sobre como a conta da crise climática deixou de ser um debate técnico e virou disputa entre Norte e Sul. O texto reconstrói 15 anos de promessas não cumpridas e explica o que está em jogo na votação de hoje.",
            "source": "ANÁLISE · O MATINAL",
            "minutes": 6,
        },
    }


def weather_exemplo() -> Weather:
    return Weather(
        temp_atual="26°", icon="cloud-sun", condicao="Sol entre nuvens, brisa do mar",
        maxima="30°", minima="24°",
        linha_sensacao="Sensação térmica 29° · Umidade 74% · Vento 18 km/h de leste",
        horaria=[
            HourForecast("06h", "sunrise", "24°", "10%"),
            HourForecast("09h", "sun", "27°", "5%"),
            HourForecast("12h", "cloud-sun", "30°", "15%"),
            HourForecast("15h", "cloud-sun", "29°", "20%"),
            HourForecast("18h", "sunset", "27°", "20%"),
            HourForecast("21h", "cloud", "25°", "10%"),
        ],
        nascer_por_sol="05:14 / 17:19", indice_uv="9 · muito alto",
        mar="Ondas até 1,6 m", semana="24° a 31° nos próximos dias",
        resumo_curto="Sol entre nuvens · 24° / 30° · chuva 20%", ok=True,
    )


def numeros_exemplo() -> list[MarketNumber]:
    return [
        MarketNumber("DÓLAR", "R$ 5,12", "-0,4%", "down"),
        MarketNumber("IBOVESPA", "141.208", "+0,8%", "up"),
        MarketNumber("SELIC", "12,25%", "estável", "flat"),
        MarketNumber("BITCOIN", "US$ 118,4k", "+2,1%", "up"),
        MarketNumber("IPCA 12 MESES", "4,1%", "—", "flat", sem_delta=True),
    ]
