"""Coleta das redes Wi-Fi vizinhas no macOS (CoreWLAN ou `system_profiler`)."""

from __future__ import annotations

import json
import logging
import re
import subprocess
from dataclasses import dataclass
from typing import Any

LOGGER_NAME = "WIFI"
"""Nome do logger da tool. Configure com `setup_logger(LOGGER_NAME)` para ver o progresso."""

BANDAS_COREWLAN = {1: "2.4", 2: "5", 3: "6"}
"""Valores de `CWChannelBand` do CoreWLAN para a banda em GHz."""

LARGURAS_COREWLAN = {1: 20, 2: 40, 3: 80, 4: 160}
"""Valores de `CWChannelWidth` do CoreWLAN para a largura em MHz."""

METODO_COREWLAN = "CoreWLAN (com sinal real)"
"""Descrição do método de coleta quando o CoreWLAN está disponível."""

METODO_PROFILER = "system_profiler (sem sinal das vizinhas)"
"""Descrição do método de coleta de reserva."""

logger = logging.getLogger(LOGGER_NAME)


@dataclass(frozen=True)
class Rede:
    """Uma rede Wi-Fi vista num scan."""

    canal: int
    largura: int
    banda: str
    rssi: int | None = None
    """Sinal em dBm (mais perto de zero = mais forte). `None` quando o macOS esconde."""


def banda_por_canal(canal: int) -> str:
    """
    Deduz a banda pelo número do canal, para quando o macOS não informa.

    ! Ambíguo para redes de 6 GHz, que reusam números de canal do 2.4 e do 5 GHz.

    Args:
        canal: número do canal.

    Returns:
        `"2.4"` ou `"5"`.
    """

    return "2.4" if canal <= 14 else "5"


def parsear_canal(texto: str) -> tuple[int, str, int] | None:
    """
    Interpreta o canal no formato do `system_profiler`, ex.: `"36 (5GHz, 80MHz)"`.

    Args:
        texto: valor de `spairport_network_channel`.

    Returns:
        `(canal, banda, largura)`, ou `None` se o texto não começar com um número.
    """

    m = re.match(r"\s*(\d+)", texto)
    if not m:
        return None
    canal = int(m.group(1))

    banda_m = re.search(r"(\d)\s*GHz", texto)
    banda = {"2": "2.4", "5": "5", "6": "6"}.get(banda_m.group(1)) if banda_m else None

    largura_m = re.search(r"(\d+)\s*MHz", texto)
    largura = int(largura_m.group(1)) if largura_m else 20

    return canal, banda or banda_por_canal(canal), largura


def _sinal(info: dict[str, Any]) -> int | None:
    """Extrai o RSSI de `spairport_signal_noise` (`"-39 dBm / -96 dBm"`), se existir."""

    m = re.search(r"(-\d+)\s*dBm", str(info.get("spairport_signal_noise", "")))
    return int(m.group(1)) if m else None


def _rede_do_profiler(info: dict[str, Any]) -> Rede | None:
    """Converte um item do `system_profiler` em `Rede` (ou `None` se não tiver canal)."""

    parsed = parsear_canal(str(info.get("spairport_network_channel", "")))
    if parsed is None:
        return None
    canal, banda, largura = parsed
    return Rede(canal=canal, largura=largura, banda=banda, rssi=_sinal(info))


def _interfaces(dados: dict[str, Any]) -> list[dict[str, Any]]:
    """Lista as interfaces Wi-Fi do JSON do `system_profiler`."""

    return [
        itf
        for bloco in dados.get("SPAirPortDataType", [])
        for itf in bloco.get("spairport_airport_interfaces", [])
    ]


def redes_do_profiler(dados: dict[str, Any]) -> list[Rede]:
    """
    Extrai as redes vizinhas do JSON do `system_profiler SPAirPortDataType -json`.

    * Desde o macOS 14.4 o sinal das vizinhas não vem mais aqui: `rssi` fica `None`.

    Args:
        dados: JSON já carregado.

    Returns:
        Redes vizinhas (a rede conectada não entra).
    """

    redes = []
    for itf in _interfaces(dados):
        for info in itf.get("spairport_airport_other_local_wireless_networks", []):
            rede = _rede_do_profiler(info)
            if rede is not None:
                redes.append(rede)
    return redes


def rede_atual_do_profiler(dados: dict[str, Any]) -> Rede | None:
    """
    Extrai a rede em que o Mac está conectado, com canal e sinal.

    Args:
        dados: JSON já carregado do `system_profiler`.

    Returns:
        A rede conectada, ou `None` se o Wi-Fi estiver desconectado.
    """

    for itf in _interfaces(dados):
        info = itf.get("spairport_current_network_information")
        if info:
            rede = _rede_do_profiler(info)
            if rede is not None:
                return rede
    return None


def ler_profiler() -> dict[str, Any]:
    """
    Roda o `system_profiler` e devolve o JSON da parte de Wi-Fi.

    Returns:
        JSON carregado (vazio se o comando não devolver nada).

    Raises:
        FileNotFoundError: fora do macOS.
    """

    saida = subprocess.run(
        ["system_profiler", "SPAirPortDataType", "-json"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    return json.loads(saida) if saida.strip() else {}


def interface_corewlan() -> Any | None:
    """
    Abre a interface Wi-Fi padrão via CoreWLAN.

    Returns:
        Objeto `CWInterface`, ou `None` se o pyobjc não estiver instalado (extra `wifi`)
        ou o Mac não tiver Wi-Fi.
    """

    try:
        import CoreWLAN  # type: ignore[import-not-found]
    except ImportError:
        return None
    return CoreWLAN.CWWiFiClient.sharedWiFiClient().interface()


def redes_do_corewlan(interface: Any) -> list[Rede]:
    """
    Faz um scan ativo pelo CoreWLAN, que informa o sinal real de cada rede.

    Args:
        interface: `CWInterface` de `interface_corewlan`.

    Returns:
        Redes vistas no scan.

    Raises:
        RuntimeError: se o scan falhar (Wi-Fi desligado, por exemplo).
    """

    resultado, erro = interface.scanForNetworksWithName_error_(None, None)
    if resultado is None:
        raise RuntimeError(f"Scan do CoreWLAN falhou: {erro}")

    redes = []
    for rede in resultado:
        canal = rede.wlanChannel()
        if canal is None:
            continue
        numero = int(canal.channelNumber())
        redes.append(
            Rede(
                canal=numero,
                largura=LARGURAS_COREWLAN.get(int(canal.channelWidth()), 20),
                banda=BANDAS_COREWLAN.get(
                    int(canal.channelBand()), banda_por_canal(numero)
                ),
                rssi=int(rede.rssiValue()),
            )
        )
    return redes


class Scanner:
    """Escolhe o melhor método disponível e faz os scans."""

    def __init__(self, usar_corewlan: bool = True) -> None:
        """
        Args:
            usar_corewlan: `False` força o `system_profiler`, mesmo com o CoreWLAN instalado.
        """

        self.interface = interface_corewlan() if usar_corewlan else None

    @property
    def metodo(self) -> str:
        """Descrição do método de coleta em uso."""

        return METODO_COREWLAN if self.interface is not None else METODO_PROFILER

    def escanear(self) -> list[Rede]:
        """
        Faz um scan das redes vizinhas.

        * Se o CoreWLAN falhar num scan, esse scan cai para o `system_profiler`.

        Returns:
            Redes vistas.
        """

        if self.interface is not None:
            try:
                return redes_do_corewlan(self.interface)
            except Exception as erro:  # noqa: BLE001 — pyobjc pode lançar qualquer coisa
                logger.warning("CoreWLAN falhou (%s); usando system_profiler", erro)
        return redes_do_profiler(ler_profiler())

    def rede_atual(self) -> Rede | None:
        """
        Rede em que o Mac está conectado.

        Returns:
            A rede conectada, ou `None` se desconectado.
        """

        return rede_atual_do_profiler(ler_profiler())
