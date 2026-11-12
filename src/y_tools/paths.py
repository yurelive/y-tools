"""
Caminhos do projeto, resolvidos a partir da raiz do repositório.

! Caminhos relativos resolvem a partir do diretório de trabalho do processo.
! Notebooks rodam de `notebooks/` e a CLI da raiz: com caminhos relativos cada um
! gravaria num lugar diferente. Por isso tudo aqui é absoluto.
"""

import os
from pathlib import Path

RAIZ = Path(os.getenv("YTOOLS_RAIZ") or Path(__file__).resolve().parents[2])
"""Raiz do repositório. Sobrescreva com a env var `YTOOLS_RAIZ` se o pacote não estiver em modo editável."""

DATA_DIR = RAIZ / "data"
"""Arquivos de entrada (áudios etc.). Fora do git."""

OUTPUT_DIR = RAIZ / "output"
"""Arquivos gerados pelas tools. Fora do git."""

LOGS_DIR = RAIZ / "logs"
"""Logs das execuções. Fora do git."""
