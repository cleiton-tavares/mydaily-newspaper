"""O Matinal — gerador de jornal matinal personalizado.

Coleta notícias (RSS), clima (Open-Meteo) e indicadores (APIs públicas),
usa uma LLM via LiteLLM para escrever o conteúdo editorial, monta as duas
páginas A4 a partir dos templates e envia para a impressora.
"""

__version__ = "1.0.0"
