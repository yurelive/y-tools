"""
CLI do monitor de Wi-Fi.

Exemplos:

    python -m y_tools.wifi                    # 30 min, um scan por minuto
    python -m y_tools.wifi --minutos 0        # um scan só, na hora
    python -m y_tools.wifi -m 60 -i 30        # 1 h, um scan a cada 30 s
    python -m y_tools.wifi --meus-canais 2.4:11
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from ..logger import setup_logger
from ..paths import OUTPUT_DIR
from .analise import FORTE_DBM, PROPRIO_DBM, parsear_meus_canais
from .coleta import LOGGER_NAME, Scanner
from .monitor import (
    INTERVALO_PADRAO,
    MINUTOS_PADRAO,
    manter_acordado,
    monitorar,
    notificar,
)


def criar_parser() -> argparse.ArgumentParser:
    """Monta o parser de argumentos da CLI."""

    parser = argparse.ArgumentParser(
        prog="python -m y_tools.wifi",
        description="Monitora as redes Wi-Fi vizinhas (macOS) e sugere os canais menos congestionados.",
    )
    parser.add_argument(
        "-m",
        "--minutos",
        type=float,
        default=MINUTOS_PADRAO,
        help=f"duração do monitoramento; 0 faz um scan só (padrão: {MINUTOS_PADRAO:.0f})",
    )
    parser.add_argument(
        "-i",
        "--intervalo",
        type=float,
        default=INTERVALO_PADRAO,
        help=f"segundos entre scans (padrão: {INTERVALO_PADRAO:.0f})",
    )
    parser.add_argument(
        "-o",
        "--saida",
        type=Path,
        default=OUTPUT_DIR,
        help="pasta do relatório e do CSV (padrão: output/)",
    )
    parser.add_argument(
        "--meus-canais",
        type=parsear_meus_canais,
        default=os.getenv("YTOOLS_WIFI_MEUS_CANAIS", ""),
        help="canais do seu roteador, ex.: 2.4:11,5:149. O da rede conectada é detectado "
        "sozinho; informe o da outra banda (padrão: env var YTOOLS_WIFI_MEUS_CANAIS)",
    )
    parser.add_argument(
        "--nao-detectar-conectada",
        action="store_true",
        help="não usa a rede conectada como canal do seu roteador",
    )
    parser.add_argument(
        "--proprio-dbm",
        type=int,
        default=PROPRIO_DBM,
        help=f"sinal acima disso, no canal do roteador, é o seu roteador (padrão: {PROPRIO_DBM})",
    )
    parser.add_argument(
        "--forte-dbm",
        type=int,
        default=FORTE_DBM,
        help=f"sinal acima disso conta como vizinho forte (padrão: {FORTE_DBM})",
    )
    parser.add_argument(
        "--sem-corewlan",
        action="store_true",
        help="força o system_profiler (sem sinal das vizinhas)",
    )
    parser.add_argument(
        "--sem-notificacao", action="store_true", help="não notifica no fim"
    )
    parser.add_argument("--debug", action="store_true", help="logs em nível DEBUG")

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Ponto de entrada da CLI.

    Args:
        argv: argumentos (sem o nome do programa). `None` usa `sys.argv`.

    Returns:
        Código de saída: 0 em sucesso, 1 se nenhum scan der certo.
    """

    load_dotenv()
    args = criar_parser().parse_args(argv)
    logger = setup_logger(LOGGER_NAME, debug=args.debug or None)

    manter_acordado()
    resultado = monitorar(
        minutos=args.minutos,
        intervalo=args.intervalo,
        destino=args.saida,
        scanner=Scanner(usar_corewlan=not args.sem_corewlan),
        proprio_dbm=args.proprio_dbm,
        forte_dbm=args.forte_dbm,
        meus_canais=args.meus_canais,
        detectar_conectada=not args.nao_detectar_conectada,
    )

    if resultado.analise.n_scans == 0:
        logger.error("Nenhum scan deu certo. Confira se o Wi-Fi do Mac está ligado.")
        return 1

    logger.info("\n%s", resultado.relatorio)
    logger.info("Relatório salvo em %s", resultado.arquivo_txt)

    if not args.sem_notificacao:
        analise = resultado.analise
        notificar(
            "Scan Wi-Fi terminou",
            f"2.4 GHz: canal {analise.melhor_24()} | 5 GHz: bloco {analise.melhor_5()}",
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
