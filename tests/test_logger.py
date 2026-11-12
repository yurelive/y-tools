import logging
from datetime import datetime

import pytest

from y_tools.logger import setup_logger


@pytest.fixture(autouse=True)
def _limpa_loggers():
    """Evita que um teste herde handlers configurados por outro."""
    yield
    for nome in list(logging.Logger.manager.loggerDict):
        logging.getLogger(nome).handlers.clear()


def test_grava_arquivo_com_nome_da_tool(tmp_path):
    logger = setup_logger("TRANSCRICAO", log_folder=tmp_path)
    logger.info("mensagem de teste")

    arquivo = tmp_path / f"transcricao_{datetime.now().strftime('%Y%m%d')}.log"
    assert "mensagem de teste" in arquivo.read_text(encoding="utf-8")


def test_nao_acumula_handlers(tmp_path):
    setup_logger("X", log_folder=tmp_path)
    logger = setup_logger("X", log_folder=tmp_path)

    assert len(logger.handlers) == 2
    assert logger.propagate is False


def test_debug_pela_env(tmp_path, monkeypatch):
    monkeypatch.setenv("YTOOLS_DEBUG", "true")

    assert setup_logger("X", log_folder=tmp_path).level == logging.DEBUG
    assert setup_logger("X", log_folder=tmp_path, debug=False).level == logging.INFO
