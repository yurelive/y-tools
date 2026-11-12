from functools import partial

import pytest

from y_tools.logger import setup_logger
from y_tools.transcricao import listar_audios, transcrever_audio
from y_tools.transcricao.__main__ import main


@pytest.fixture
def audio(tmp_path):
    """Arquivo qualquer: o Whisper é fake, o conteúdo não importa."""
    arquivo = tmp_path / "nota.ogg"
    arquivo.write_bytes(b"fake")
    return arquivo


@pytest.fixture
def logs_em_tmp(monkeypatch, tmp_path):
    """A CLI grava log em arquivo: nos testes, numa pasta temporária."""
    monkeypatch.setattr(
        "y_tools.transcricao.__main__.setup_logger",
        partial(setup_logger, log_folder=tmp_path / "logs"),
    )


def test_monta_transcricao(whisper_fake, audio):
    resultado = transcrever_audio(audio, modelo="tiny")

    assert resultado.arquivo == audio.resolve()
    assert resultado.idioma == "pt"
    assert resultado.duracao == 10.0
    assert resultado.modelo == "tiny"
    assert [s.texto for s in resultado.segmentos] == ["Olá, tudo bem?", "Tudo ótimo."]
    assert resultado.texto == "Olá, tudo bem? Tudo ótimo."


def test_repassa_parametros_ao_whisper(whisper_fake, audio):
    transcrever_audio(audio, idioma=None, vad=False, beam_size=1)

    caminho, kwargs = whisper_fake.chamadas[0]
    assert caminho == str(audio.resolve())
    assert kwargs == {"language": None, "vad_filter": False, "beam_size": 1}


def test_arquivo_inexistente(whisper_fake, tmp_path):
    with pytest.raises(FileNotFoundError):
        transcrever_audio(tmp_path / "nao_existe.mp3")

    assert whisper_fake.chamadas == []


def test_listar_audios_filtra_extensoes(tmp_path):
    for nome in ["b.MP3", "a.m4a", "notas.txt", "c.opus"]:
        (tmp_path / nome).write_bytes(b"")
    (tmp_path / "sub.wav").mkdir()

    assert [p.name for p in listar_audios(tmp_path)] == ["a.m4a", "b.MP3", "c.opus"]


def test_cli_gera_os_formatos_pedidos(whisper_fake, audio, tmp_path, logs_em_tmp):
    saida = tmp_path / "out"

    codigo = main(
        [str(audio), "-f", "srt", "-f", "txt", "-o", str(saida), "-i", "auto"]
    )

    assert codigo == 0
    assert sorted(p.name for p in saida.iterdir()) == ["nota.srt", "nota.txt"]
    assert whisper_fake.chamadas[0][1]["language"] is None


def test_cli_pasta_vazia_retorna_erro(whisper_fake, tmp_path, logs_em_tmp):

    assert main([str(tmp_path)]) == 1
