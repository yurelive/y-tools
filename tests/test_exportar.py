import json

import pytest

from y_tools.transcricao import (
    de_json,
    formatar_tempo,
    para_json,
    para_srt,
    para_txt,
    para_vtt,
    salvar,
)


@pytest.mark.parametrize(
    ("segundos", "esperado"),
    [
        (0, "00:00:00,000"),
        (62.5, "00:01:02,500"),
        (3725.0015, "01:02:05,002"),
        (1.9999, "00:00:02,000"),  # ! arredondar não pode gerar ",1000"
        (-1, "00:00:00,000"),
    ],
)
def test_formatar_tempo(segundos, esperado):
    assert formatar_tempo(segundos) == esperado


def test_formatar_tempo_vtt_usa_ponto():
    assert formatar_tempo(62.5, ".") == "00:01:02.500"


def test_para_txt_um_segmento_por_linha(transcricao):
    assert para_txt(transcricao) == "Bom dia a todos.\nVamos começar.\n"


def test_para_srt(transcricao):
    assert para_srt(transcricao) == (
        "1\n00:00:00,000 --> 00:00:02,500\nBom dia a todos.\n"
        "\n"
        "2\n00:01:02,500 --> 01:02:05,002\nVamos começar.\n"
    )


def test_para_vtt(transcricao):
    vtt = para_vtt(transcricao)

    assert vtt.startswith("WEBVTT\n\n")
    assert "00:01:02.500 --> 01:02:05.002\nVamos começar." in vtt


def test_para_json_round_trip(transcricao):
    conteudo = para_json(transcricao)
    dados = json.loads(conteudo)
    reconstruida = de_json(conteudo)

    assert dados["texto"] == "Bom dia a todos. Vamos começar."
    assert dados["arquivo"] == "reuniao.m4a"
    assert reconstruida.segmentos[0] == transcricao.segmentos[0]
    assert reconstruida.idioma == "pt"


@pytest.mark.parametrize("formato", ["txt", "srt", "vtt", "json", ".SRT"])
def test_salvar_usa_nome_do_audio(transcricao, tmp_path, formato):
    destino = tmp_path / "saida"

    arquivo = salvar(transcricao, formato=formato, destino=destino)

    assert arquivo.parent == destino
    assert arquivo.name == f"reuniao.{formato.lower().lstrip('.')}"
    assert arquivo.read_text(encoding="utf-8")


def test_salvar_formato_invalido(transcricao, tmp_path):
    with pytest.raises(ValueError, match="não suportado"):
        salvar(transcricao, formato="docx", destino=tmp_path)
