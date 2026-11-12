"""
CLI da transcrição.

Exemplos:

    python -m y_tools.transcricao data/reuniao.m4a
    python -m y_tools.transcricao data/ --modelo medium --formato srt --formato txt
    python -m y_tools.transcricao audio.mp3 --idioma auto
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from ..logger import setup_logger
from ..paths import OUTPUT_DIR
from .exportar import FORMATOS, salvar
from .transcritor import (
    DISPOSITIVOS,
    IDIOMA_PADRAO,
    LOGGER_NAME,
    MODELO_PADRAO,
    MODELOS_DISPONIVEIS,
    listar_audios,
    transcrever_audio,
)


def criar_parser() -> argparse.ArgumentParser:
    """Monta o parser de argumentos da CLI."""

    parser = argparse.ArgumentParser(
        prog="python -m y_tools.transcricao",
        description="Transcreve áudios em texto com o Whisper rodando localmente.",
    )
    parser.add_argument(
        "entrada", type=Path, help="arquivo de áudio ou pasta com áudios"
    )
    parser.add_argument(
        "-m",
        "--modelo",
        default=MODELO_PADRAO,
        help=f"modelo do Whisper ({', '.join(MODELOS_DISPONIVEIS)})",
    )
    parser.add_argument(
        "-i",
        "--idioma",
        default=IDIOMA_PADRAO,
        help="código do idioma (pt, en...) ou 'auto' para detectar",
    )
    parser.add_argument(
        "-f",
        "--formato",
        action="append",
        choices=FORMATOS,
        help="formato de saída; repita para gerar vários (padrão: txt)",
    )
    parser.add_argument(
        "-o",
        "--saida",
        type=Path,
        default=OUTPUT_DIR,
        help="pasta de saída (padrão: output/)",
    )
    parser.add_argument(
        "-d",
        "--dispositivo",
        default="auto",
        choices=DISPOSITIVOS,
        help="onde rodar (mps = GPU do Mac, experimental)",
    )
    parser.add_argument(
        "--sem-vad", action="store_true", help="não pular trechos de silêncio"
    )
    parser.add_argument(
        "--debug", action="store_true", help="mostra cada segmento no console"
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Ponto de entrada da CLI.

    Args:
        argv: argumentos (sem o nome do programa). `None` usa `sys.argv`.

    Returns:
        Código de saída: 0 em sucesso, 1 se algum arquivo falhar.
    """

    load_dotenv()
    args = criar_parser().parse_args(argv)
    logger = setup_logger(LOGGER_NAME, debug=args.debug or None)

    if args.entrada.is_dir():
        arquivos = listar_audios(args.entrada)
        if not arquivos:
            logger.warning("Nenhum áudio encontrado em %s", args.entrada)
            return 1
    else:
        arquivos = [args.entrada]

    idioma = None if args.idioma.lower() == "auto" else args.idioma
    formatos = args.formato or ["txt"]
    falhas = 0

    for arquivo in arquivos:
        try:
            resultado = transcrever_audio(
                arquivo,
                modelo=args.modelo,
                idioma=idioma,
                vad=not args.sem_vad,
                dispositivo=args.dispositivo,
            )
        except (
            Exception
        ):  # noqa: BLE001 — num lote, um arquivo ruim não pode derrubar os outros
            logger.exception("Falha ao transcrever %s", arquivo)
            falhas += 1
            continue

        for formato in formatos:
            logger.info(
                "Salvo em %s", salvar(resultado, formato=formato, destino=args.saida)
            )

    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
