from types import SimpleNamespace

import pytest

from y_tools.wifi import (
    METODO_COREWLAN,
    METODO_PROFILER,
    Rede,
    Scanner,
    parsear_canal,
    rede_atual_do_profiler,
    redes_do_corewlan,
    redes_do_profiler,
)

PROFILER = {
    "SPAirPortDataType": [
        {
            "spairport_airport_interfaces": [
                {
                    "spairport_current_network_information": {
                        "spairport_network_channel": "36 (5GHz, 80MHz)",
                        "spairport_signal_noise": "-39 dBm / -96 dBm",
                    },
                    "spairport_airport_other_local_wireless_networks": [
                        {"spairport_network_channel": "157 (5GHz, 80MHz)"},
                        {"spairport_network_channel": "1 (2GHz, 40MHz)"},
                        {"spairport_network_channel": "37 (6GHz, 160MHz)"},
                        {
                            "spairport_network_channel": "11 (2GHz, 20MHz)",
                            "spairport_signal_noise": "-70 dBm / -95 dBm",
                        },
                        {"spairport_network_channel": ""},
                    ],
                }
            ]
        }
    ]
}
"""Recorte do JSON real do `system_profiler SPAirPortDataType -json`."""


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("36 (5GHz, 80MHz)", (36, "5", 80)),
        ("1 (2GHz, 40MHz)", (1, "2.4", 40)),
        ("37 (6GHz, 160MHz)", (37, "6", 160)),
        ("11", (11, "2.4", 20)),
        ("149", (149, "5", 20)),
        ("", None),
        ("desconhecido", None),
    ],
)
def test_parsear_canal(texto, esperado):
    assert parsear_canal(texto) == esperado


def test_redes_do_profiler():
    assert redes_do_profiler(PROFILER) == [
        Rede(canal=157, largura=80, banda="5"),
        Rede(canal=1, largura=40, banda="2.4"),
        Rede(canal=37, largura=160, banda="6"),
        Rede(canal=11, largura=20, banda="2.4", rssi=-70),
    ]


def test_rede_atual_do_profiler():
    assert rede_atual_do_profiler(PROFILER) == Rede(
        canal=36, largura=80, banda="5", rssi=-39
    )


def test_profiler_vazio():
    assert redes_do_profiler({}) == []
    assert rede_atual_do_profiler({}) is None


def _rede_cw(canal, largura, banda, rssi):
    """Imita um `CWNetwork` do pyobjc."""
    ch = SimpleNamespace(
        channelNumber=lambda: canal,
        channelWidth=lambda: largura,
        channelBand=lambda: banda,
    )
    return SimpleNamespace(wlanChannel=lambda: ch, rssiValue=lambda: rssi)


class InterfaceFake:
    """Imita o `CWInterface.scanForNetworksWithName_error_`."""

    def __init__(self, redes=None, erro=None):
        self.redes = redes
        self.erro = erro

    def scanForNetworksWithName_error_(self, nome, erro):
        return self.redes, self.erro


def test_redes_do_corewlan_converte_enums():
    interface = InterfaceFake(
        [_rede_cw(6, 1, 1, -80), _rede_cw(100, 4, 2, -60), _rede_cw(5, 3, 3, -70)]
    )

    assert redes_do_corewlan(interface) == [
        Rede(canal=6, largura=20, banda="2.4", rssi=-80),
        Rede(canal=100, largura=160, banda="5", rssi=-60),
        Rede(canal=5, largura=80, banda="6", rssi=-70),
    ]


def test_redes_do_corewlan_erro():
    with pytest.raises(RuntimeError, match="falhou"):
        redes_do_corewlan(InterfaceFake(redes=None, erro="Wi-Fi desligado"))


def test_scanner_sem_corewlan_usa_profiler(monkeypatch):
    monkeypatch.setattr("y_tools.wifi.coleta.ler_profiler", lambda: PROFILER)

    scanner = Scanner(usar_corewlan=False)

    assert scanner.metodo == METODO_PROFILER
    assert len(scanner.escanear()) == 4
    assert scanner.rede_atual().canal == 36


def test_scanner_cai_para_profiler_se_corewlan_falhar(monkeypatch):
    monkeypatch.setattr("y_tools.wifi.coleta.ler_profiler", lambda: PROFILER)
    monkeypatch.setattr(
        "y_tools.wifi.coleta.interface_corewlan",
        lambda: InterfaceFake(redes=None, erro="ocupado"),
    )

    scanner = Scanner()

    assert scanner.metodo == METODO_COREWLAN
    assert len(scanner.escanear()) == 4
