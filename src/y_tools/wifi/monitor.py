"""Monitoramento contínuo: vários scans ao longo do tempo, CSV bruto e relatório."""

from __future__ import annotations

import csv
import logging
import os
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..paths import OUTPUT_DIR
from .analise import FORTE_DBM, PROPRIO_DBM, Analise, formatar_relatorio
from .coleta import LOGGER_NAME, Rede, Scanner

MINUTOS_PADRAO = 30.0
"""Duração padrão do monitoramento, em minutos."""

INTERVALO_PADRAO = 60.0
"""Intervalo padrão entre scans, em segundos."""

COLUNAS_CSV = ("horario", "scan", "banda", "canal", "largura_mhz", "rssi_dbm")
"""Cabeçalho do CSV com os dados brutos (uma linha por rede por scan)."""

logger = logging.getLogger(LOGGER_NAME)


@dataclass
class Monitoramento:
    """Resultado de um monitoramento."""

    analise: Analise
    metodo: str
    relatorio: str
    arquivo_txt: Path
    arquivo_csv: Path
    rede_atual: Rede | None = None


def manter_acordado() -> subprocess.Popen | None:
    """
    Impede o Mac de dormir enquanto este processo existir (`caffeinate -i -w <pid>`).

    Returns:
        Processo do `caffeinate`, ou `None` fora do macOS.
    """

    try:
        return subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])
    except FileNotFoundError:
        logger.debug("caffeinate não disponível; o computador pode dormir")
        return None


def notificar(titulo: str, mensagem: str) -> None:
    """
    Mostra uma notificação do macOS com som. Não faz nada fora do macOS.

    Args:
        titulo: título da notificação.
        mensagem: corpo da notificação.
    """

    def _escapar(texto: str) -> str:
        return texto.replace("\\", "\\\\").replace('"', '\\"')

    script = (
        f'display notification "{_escapar(mensagem)}" '
        f'with title "{_escapar(titulo)}" sound name "Glass"'
    )
    try:
        subprocess.run(["osascript", "-e", script], check=False, capture_output=True)
    except FileNotFoundError:
        logger.debug("osascript não disponível; sem notificação")


def monitorar(
    minutos: float = MINUTOS_PADRAO,
    intervalo: float = INTERVALO_PADRAO,
    destino: str | Path = OUTPUT_DIR,
    scanner: Scanner | None = None,
    proprio_dbm: int = PROPRIO_DBM,
    forte_dbm: int = FORTE_DBM,
    dormir: Callable[[float], None] = time.sleep,
    relogio: Callable[[], float] = time.monotonic,
) -> Monitoramento:
    """
    Faz scans periódicos, grava o CSV bruto e gera o relatório no fim.

    * `minutos=0` faz um único scan.
    * Ctrl+C encerra antes da hora e ainda gera o relatório com o que foi coletado.
    * Um scan que falha é registrado no log e não derruba o monitoramento.

    Args:
        minutos: duração total.
        intervalo: segundos entre scans.
        destino: pasta dos arquivos gerados (criada se não existir).
        scanner: scanner a usar. `None` cria um com o melhor método disponível.
        proprio_dbm: sinal acima disso é tratado como o seu roteador.
        forte_dbm: sinal acima disso conta como vizinho forte.
        dormir: função de espera (substituível nos testes).
        relogio: relógio monotônico (substituível nos testes).

    Returns:
        Análise, relatório e caminhos dos arquivos gerados.
    """

    scanner = scanner or Scanner()
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo_csv = destino / f"wifi_scans_{carimbo}.csv"
    arquivo_txt = destino / f"wifi_relatorio_{carimbo}.txt"

    rede_atual = _rede_atual(scanner)
    analise = Analise(proprio_dbm=proprio_dbm, forte_dbm=forte_dbm)
    fim = relogio() + minutos * 60

    logger.info("Método: %s", scanner.metodo)
    logger.info("Rodando por %.0f min, scan a cada %.0fs (Ctrl+C encerra)", minutos, intervalo)

    with open(arquivo_csv, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(COLUNAS_CSV)
        try:
            while True:
                agora = datetime.now().strftime("%H:%M:%S")
                try:
                    redes = scanner.escanear()
                except Exception:  # noqa: BLE001 — num monitoramento longo, um scan ruim não para tudo
                    logger.exception("Scan falhou às %s", agora)
                else:
                    analise.adicionar(redes)
                    for r in redes:
                        escritor.writerow(
                            [agora, analise.n_scans, r.banda, r.canal, r.largura, r.rssi]
                        )
                    f.flush()
                    logger.info("%s  scan %d: %d redes", agora, analise.n_scans, len(redes))

                if relogio() + intervalo >= fim:
                    break
                dormir(intervalo)
        except KeyboardInterrupt:
            logger.warning("Interrompido: gerando relatório com %d scans", analise.n_scans)

    relatorio = (
        f"Relatório Wi-Fi — {datetime.now():%d/%m/%Y %H:%M}\n"
        + formatar_relatorio(analise, scanner.metodo, minutos, rede_atual)
        + f"\n\nDados brutos: {arquivo_csv}"
    )
    arquivo_txt.write_text(relatorio, encoding="utf-8")

    return Monitoramento(
        analise=analise,
        metodo=scanner.metodo,
        relatorio=relatorio,
        arquivo_txt=arquivo_txt,
        arquivo_csv=arquivo_csv,
        rede_atual=rede_atual,
    )


def _rede_atual(scanner: Scanner) -> Rede | None:
    """Rede conectada, sem deixar uma falha aqui impedir o monitoramento."""

    try:
        return scanner.rede_atual()
    except Exception:  # noqa: BLE001 — é só informativo
        logger.debug("Não foi possível ler a rede atual", exc_info=True)
        return None
