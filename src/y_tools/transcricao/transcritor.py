"""Transcrição de áudio em texto com faster-whisper (Whisper rodando localmente)."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

LOGGER_NAME = "TRANSCRICAO"
"""Nome do logger da tool. Configure com `setup_logger(LOGGER_NAME)` para ver o progresso."""

MODELOS_DISPONIVEIS = ("tiny", "base", "small", "medium", "large-v3", "turbo")
"""Modelos do Whisper, do mais rápido/impreciso ao mais lento/preciso."""

MODELO_PADRAO = os.getenv("YTOOLS_MODELO_WHISPER", "small")
"""Modelo usado quando nenhum é informado. Sobrescreva com a env var `YTOOLS_MODELO_WHISPER`."""

DISPOSITIVOS = ("auto", "cpu", "mps", "cuda")
"""Onde o modelo roda. `auto` usa CUDA se houver, senão CPU. `mps` (GPU do Apple Silicon) é experimental."""

IDIOMA_PADRAO = "pt"
"""Idioma padrão do áudio. `None` faz o Whisper detectar sozinho."""

EXTENSOES_SUPORTADAS = frozenset(
    {".mp3", ".wav", ".m4a", ".ogg", ".opus", ".flac", ".webm", ".mp4", ".aiff", ".aac"}
)
"""Extensões reconhecidas ao transcrever uma pasta. O PyAV decodifica todas sem ffmpeg instalado."""

logger = logging.getLogger(LOGGER_NAME)


@dataclass(frozen=True)
class Segmento:
    """Trecho contínuo de fala, com início e fim em segundos."""

    inicio: float
    fim: float
    texto: str


@dataclass
class Transcricao:
    """Resultado da transcrição de um arquivo de áudio."""

    arquivo: Path
    idioma: str
    duracao: float
    segmentos: list[Segmento] = field(default_factory=list)
    modelo: str = MODELO_PADRAO
    tempo_processamento: float = 0.0

    @property
    def texto(self) -> str:
        """Texto completo, com os segmentos separados por espaço."""

        return " ".join(s.texto for s in self.segmentos if s.texto)


@lru_cache(maxsize=2)
def carregar_modelo(
    modelo: str = MODELO_PADRAO, dispositivo: str = "auto", compute_type: str = "int8"
) -> WhisperModel:
    """
    Carrega (e guarda em cache) um modelo do Whisper.

    * Na primeira vez o modelo é baixado do Hugging Face para `~/.cache/huggingface`.
    * O cache em memória evita recarregar o modelo a cada célula do notebook.

    Args:
        modelo: nome do modelo (ver `MODELOS_DISPONIVEIS`) ou caminho de um modelo local.
        dispositivo: um de `DISPOSITIVOS`. No Mac, `auto` usa a CPU.
        compute_type: precisão dos pesos. `int8` é o melhor custo/benefício em CPU.

    Returns:
        Modelo pronto para transcrever.
    """

    from faster_whisper import WhisperModel

    logger.info("Carregando modelo '%s' (%s, %s)", modelo, dispositivo, compute_type)

    return WhisperModel(modelo, device=dispositivo, compute_type=compute_type)


def transcrever_audio(
    caminho: str | Path,
    modelo: str = MODELO_PADRAO,
    idioma: str | None = IDIOMA_PADRAO,
    vad: bool = True,
    beam_size: int = 5,
    dispositivo: str = "auto",
) -> Transcricao:
    """
    Transcreve um arquivo de áudio em texto.

    Args:
        caminho: arquivo de áudio (qualquer formato suportado pelo PyAV).
        modelo: modelo do Whisper. Ver `MODELOS_DISPONIVEIS`.
        idioma: código do idioma (`pt`, `en`...). `None` detecta automaticamente.
        vad: `True` pula trechos de silêncio — mais rápido e evita texto "inventado".
        beam_size: largura do beam search. Maior é mais preciso e mais lento.
        dispositivo: um de `DISPOSITIVOS`. Teste `mps` em áudios longos no Mac.

    Returns:
        Transcrição com o texto, os segmentos e metadados.

    Raises:
        FileNotFoundError: se o arquivo não existir.
    """

    caminho = Path(caminho).expanduser().resolve()
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo de áudio não encontrado: {caminho}")

    whisper = carregar_modelo(modelo, dispositivo)

    logger.info("Transcrevendo %s", caminho.name)
    inicio = time.perf_counter()

    # * `segmentos` é um gerador: a transcrição de fato acontece ao iterar
    gerador, info = whisper.transcribe(
        str(caminho), language=idioma, vad_filter=vad, beam_size=beam_size
    )

    if idioma is None:
        logger.info(
            "Idioma detectado: %s (%.0f%%)",
            info.language,
            info.language_probability * 100,
        )

    segmentos: list[Segmento] = []
    ultimo_marco = 0
    for seg in gerador:
        segmentos.append(
            Segmento(inicio=seg.start, fim=seg.end, texto=seg.text.strip())
        )
        logger.debug("[%.1fs -> %.1fs] %s", seg.start, seg.end, seg.text.strip())

        # * Loga o progresso a cada 10% do áudio
        if info.duration:
            marco = int(seg.end / info.duration * 10)
            if marco > ultimo_marco:
                ultimo_marco = marco
                logger.info("Progresso: %d%%", min(marco * 10, 100))

    tempo = time.perf_counter() - inicio
    logger.info("Concluído em %.1fs (áudio de %.1fs)", tempo, info.duration)

    return Transcricao(
        arquivo=caminho,
        idioma=info.language,
        duracao=info.duration,
        segmentos=segmentos,
        modelo=modelo,
        tempo_processamento=tempo,
    )


def listar_audios(pasta: str | Path) -> list[Path]:
    """
    Lista os arquivos de áudio de uma pasta (sem recursão), em ordem alfabética.

    Args:
        pasta: pasta a ser varrida.

    Returns:
        Arquivos com extensão em `EXTENSOES_SUPORTADAS`.
    """

    return sorted(
        p
        for p in Path(pasta).iterdir()
        if p.is_file() and p.suffix.lower() in EXTENSOES_SUPORTADAS
    )
