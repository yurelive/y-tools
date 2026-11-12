from pathlib import Path
from types import SimpleNamespace

import pytest

from y_tools.transcricao import Segmento, Transcricao


@pytest.fixture
def transcricao() -> Transcricao:
    """Transcrição pronta, sem passar pelo Whisper."""
    return Transcricao(
        arquivo=Path("/tmp/reuniao.m4a"),
        idioma="pt",
        duracao=65.0,
        modelo="tiny",
        segmentos=[
            Segmento(inicio=0.0, fim=2.5, texto="Bom dia a todos."),
            Segmento(inicio=62.5, fim=3725.0015, texto="Vamos começar."),
        ],
    )


class WhisperFake:
    """Imita o `WhisperModel.transcribe`: devolve um gerador de segmentos e o `info`."""

    def __init__(self, segmentos, idioma="pt", duracao=10.0):
        self.segmentos = segmentos
        self.info = SimpleNamespace(
            language=idioma, language_probability=0.98, duration=duracao
        )
        self.chamadas = []

    def transcribe(self, caminho, **kwargs):
        self.chamadas.append((caminho, kwargs))
        gerador = (
            SimpleNamespace(start=i, end=f, text=t) for i, f, t in self.segmentos
        )
        return gerador, self.info


@pytest.fixture
def whisper_fake(monkeypatch) -> WhisperFake:
    """Substitui o carregamento do modelo por um fake — os testes nunca baixam modelos."""
    fake = WhisperFake([(0.0, 4.0, " Olá, tudo bem? "), (4.0, 10.0, " Tudo ótimo.")])
    monkeypatch.setattr(
        "y_tools.transcricao.transcritor.carregar_modelo",
        lambda modelo, dispositivo="auto": fake,
    )
    return fake
