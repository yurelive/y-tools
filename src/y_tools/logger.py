"""Configuração de logging padronizada das tools."""

import logging
import os
from datetime import datetime
from pathlib import Path

from .paths import LOGS_DIR

FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
"""Formato do log em arquivo — inclui timestamp e nome da tool."""

CONSOLE_FORMAT = "%(levelname)s - %(message)s"
"""Formato do log em console — enxuto, o terminal já dá o contexto temporal."""

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _debug_por_env() -> bool:
    """Lê a env var `YTOOLS_DEBUG` (`true`, `1`, `sim` ativam)."""

    return os.getenv("YTOOLS_DEBUG", "").strip().lower() in {"1", "true", "sim", "yes"}


def setup_logger(
    name: str, log_folder: str | Path = LOGS_DIR, debug: bool | None = None
) -> logging.Logger:
    """
    Configura e retorna o logger de uma tool.

    Grava em `<log_folder>/<name em minúsculas>_<AAAAMMDD>.log` e espelha no
    console. Chamar de novo com o mesmo `name` reconfigura o mesmo logger — os
    handlers anteriores são descartados, não acumulados.

    Args:
        name: nome da tool. Nomeia o logger e prefixa o arquivo.
        log_folder: pasta onde os logs são gravados. Criada se não existir.
        debug: `True` baixa o nível para DEBUG. `None` lê a env var `YTOOLS_DEBUG`.

    Returns:
        Logger configurado, pronto para uso.
    """

    if debug is None:
        debug = _debug_por_env()

    # * Cria pasta de logs se não existir
    log_folder = Path(log_folder)
    log_folder.mkdir(parents=True, exist_ok=True)
    log_filename = (
        log_folder / f"{name.lower()}_{datetime.now().strftime('%Y%m%d')}.log"
    )

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # ! Remove handlers existentes para evitar duplicação
    if logger.handlers:
        for handler in logger.handlers:
            handler.close()
        logger.handlers.clear()

    # ! Desativa propagação para evitar duplicação no root logger
    logger.propagate = False

    # * Arquivo: INFO para cima, com timestamp
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(FILE_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)

    # * Console: acompanha o nível do logger
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(CONSOLE_FORMAT))
    logger.addHandler(console_handler)

    return logger
