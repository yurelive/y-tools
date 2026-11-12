"""Exportação de transcrições para TXT, SRT, VTT e JSON."""

import json
from pathlib import Path

from ..paths import OUTPUT_DIR
from .transcritor import Segmento, Transcricao

FORMATOS = ("txt", "srt", "vtt", "json")
"""Formatos de saída suportados por `salvar`."""


def formatar_tempo(segundos: float, separador: str = ",") -> str:
    """
    Converte segundos em `HH:MM:SS,mmm` (SRT) ou `HH:MM:SS.mmm` (VTT).

    Args:
        segundos: tempo em segundos.
        separador: separador dos milissegundos — `,` no SRT, `.` no VTT.

    Returns:
        Tempo formatado.
    """

    # * Arredonda uma vez, em milissegundos, para não gerar "00:00:01,1000"
    total_ms = int(round(max(segundos, 0) * 1000))
    horas, resto = divmod(total_ms, 3_600_000)
    minutos, resto = divmod(resto, 60_000)
    segs, ms = divmod(resto, 1000)

    return f"{horas:02d}:{minutos:02d}:{segs:02d}{separador}{ms:03d}"


def para_txt(transcricao: Transcricao) -> str:
    """Texto corrido, um segmento por linha."""

    return "\n".join(s.texto for s in transcricao.segmentos) + "\n"


def para_srt(transcricao: Transcricao) -> str:
    """Legenda no formato SubRip (`.srt`)."""

    blocos = [
        f"{i}\n{formatar_tempo(s.inicio)} --> {formatar_tempo(s.fim)}\n{s.texto}\n"
        for i, s in enumerate(transcricao.segmentos, start=1)
    ]

    return "\n".join(blocos)


def para_vtt(transcricao: Transcricao) -> str:
    """Legenda no formato WebVTT (`.vtt`)."""

    blocos = [
        f"{formatar_tempo(s.inicio, '.')} --> {formatar_tempo(s.fim, '.')}\n{s.texto}\n"
        for s in transcricao.segmentos
    ]

    return "WEBVTT\n\n" + "\n".join(blocos)


def para_json(transcricao: Transcricao) -> str:
    """JSON com metadados, texto completo e segmentos."""

    dados = {
        "arquivo": transcricao.arquivo.name,
        "idioma": transcricao.idioma,
        "duracao": round(transcricao.duracao, 3),
        "modelo": transcricao.modelo,
        "texto": transcricao.texto,
        "segmentos": [
            {"inicio": round(s.inicio, 3), "fim": round(s.fim, 3), "texto": s.texto}
            for s in transcricao.segmentos
        ],
    }

    return json.dumps(dados, ensure_ascii=False, indent=2) + "\n"


def de_json(conteudo: str) -> Transcricao:
    """
    Reconstrói uma `Transcricao` a partir do JSON gerado por `para_json`.

    Args:
        conteudo: texto JSON.

    Returns:
        Transcrição (o `arquivo` fica só com o nome, sem a pasta original).
    """

    dados = json.loads(conteudo)

    return Transcricao(
        arquivo=Path(dados["arquivo"]),
        idioma=dados["idioma"],
        duracao=dados["duracao"],
        modelo=dados["modelo"],
        segmentos=[Segmento(**s) for s in dados["segmentos"]],
    )


_EXPORTADORES = {"txt": para_txt, "srt": para_srt, "vtt": para_vtt, "json": para_json}


def salvar(
    transcricao: Transcricao, formato: str = "txt", destino: str | Path = OUTPUT_DIR
) -> Path:
    """
    Salva a transcrição em arquivo, com o mesmo nome do áudio.

    Args:
        transcricao: resultado de `transcrever_audio`.
        formato: um de `FORMATOS`.
        destino: pasta de saída. Criada se não existir.

    Returns:
        Caminho do arquivo gerado (`<destino>/<nome do áudio>.<formato>`).

    Raises:
        ValueError: se o formato não for suportado.
    """

    formato = formato.lower().lstrip(".")
    if formato not in _EXPORTADORES:
        raise ValueError(
            f"Formato '{formato}' não suportado. Use um de: {', '.join(FORMATOS)}"
        )

    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    arquivo = destino / f"{transcricao.arquivo.stem}.{formato}"
    arquivo.write_text(_EXPORTADORES[formato](transcricao), encoding="utf-8")

    return arquivo
