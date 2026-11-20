"""
Tool de Wi-Fi: monitora as redes vizinhas (macOS) e sugere os canais menos congestionados.

Uso rápido:

    from y_tools.wifi import Scanner, Analise, monitorar

    scanner = Scanner()
    analise = Analise()
    analise.adicionar(scanner.escanear())
    print(analise.melhores_24(), analise.melhores_5())  # mais de um quando empatam

    resultado = monitorar(minutos=30, intervalo=60)
    print(resultado.relatorio)
"""

from .analise import (
    BLOCOS_5,
    CANAIS_24,
    FORTE_DBM,
    PROPRIO_DBM,
    Analise,
    Congestionamento,
    canais_ocupados_5,
    formatar_relatorio,
    interfere_5,
    interfere_24,
    juntar,
    parsear_meus_canais,
)
from .coleta import (
    LOGGER_NAME,
    METODO_COREWLAN,
    METODO_PROFILER,
    Rede,
    Scanner,
    ler_profiler,
    parsear_canal,
    rede_atual_do_profiler,
    redes_do_corewlan,
    redes_do_profiler,
)
from .monitor import (
    INTERVALO_PADRAO,
    MINUTOS_PADRAO,
    Monitoramento,
    manter_acordado,
    monitorar,
    notificar,
)

__all__ = [
    "BLOCOS_5",
    "CANAIS_24",
    "FORTE_DBM",
    "INTERVALO_PADRAO",
    "LOGGER_NAME",
    "METODO_COREWLAN",
    "METODO_PROFILER",
    "MINUTOS_PADRAO",
    "PROPRIO_DBM",
    "Analise",
    "Congestionamento",
    "Monitoramento",
    "Rede",
    "Scanner",
    "canais_ocupados_5",
    "formatar_relatorio",
    "interfere_24",
    "interfere_5",
    "juntar",
    "ler_profiler",
    "manter_acordado",
    "monitorar",
    "notificar",
    "parsear_canal",
    "parsear_meus_canais",
    "rede_atual_do_profiler",
    "redes_do_corewlan",
    "redes_do_profiler",
]
