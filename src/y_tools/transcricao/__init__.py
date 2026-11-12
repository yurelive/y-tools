"""
Tool de transcrição: converte áudio em texto com o Whisper rodando localmente.

Uso rápido:

    from y_tools.transcricao import transcrever_audio, salvar

    resultado = transcrever_audio("data/reuniao.m4a", modelo="small")
    salvar(resultado, formato="srt")
"""

from .exportar import (
    FORMATOS,
    de_json,
    formatar_tempo,
    para_json,
    para_srt,
    para_txt,
    para_vtt,
    salvar,
)
from .transcritor import (
    DISPOSITIVOS,
    EXTENSOES_SUPORTADAS,
    IDIOMA_PADRAO,
    LOGGER_NAME,
    MODELO_PADRAO,
    MODELOS_DISPONIVEIS,
    Segmento,
    Transcricao,
    carregar_modelo,
    listar_audios,
    transcrever_audio,
)

__all__ = [
    "DISPOSITIVOS",
    "EXTENSOES_SUPORTADAS",
    "FORMATOS",
    "IDIOMA_PADRAO",
    "LOGGER_NAME",
    "MODELO_PADRAO",
    "MODELOS_DISPONIVEIS",
    "Segmento",
    "Transcricao",
    "carregar_modelo",
    "de_json",
    "formatar_tempo",
    "listar_audios",
    "para_json",
    "para_srt",
    "para_txt",
    "para_vtt",
    "salvar",
    "transcrever_audio",
]
