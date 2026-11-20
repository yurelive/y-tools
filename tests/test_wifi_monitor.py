from functools import partial

import pytest

from y_tools.logger import setup_logger
from y_tools.wifi import Rede, monitorar
from y_tools.wifi.__main__ import main


class ScannerFake:
    """Devolve scans pré-definidos; `None` na lista simula um scan que falha."""

    metodo = "fake"

    def __init__(self, scans):
        self.scans = list(scans)

    def escanear(self):
        scan = self.scans.pop(0) if self.scans else []
        if scan is None:
            raise RuntimeError("scan falhou")
        return scan

    def rede_atual(self):
        return Rede(canal=36, largura=80, banda="5", rssi=-40)


class Relogio:
    """Relógio fake: `dormir` só avança o tempo."""

    def __init__(self):
        self.t = 0.0
        self.esperas = []

    def __call__(self):
        return self.t

    def dormir(self, segundos):
        self.esperas.append(segundos)
        self.t += segundos


REDES = [Rede(canal=6, largura=20, banda="2.4", rssi=-80)]


def test_faz_scans_ate_o_fim(tmp_path):
    relogio = Relogio()

    resultado = monitorar(
        minutos=3,
        intervalo=60,
        destino=tmp_path,
        scanner=ScannerFake([REDES] * 10),
        dormir=relogio.dormir,
        relogio=relogio,
    )

    assert resultado.analise.n_scans == 3
    assert relogio.esperas == [60, 60]
    linhas = resultado.arquivo_csv.read_text().splitlines()
    assert linhas[0] == "horario,scan,banda,canal,largura_mhz,rssi_dbm"
    assert len(linhas) == 1 + 3
    assert linhas[-1].endswith(",3,2.4,6,20,-80")
    assert resultado.arquivo_txt.read_text() == resultado.relatorio
    assert "Conectado em: canal 36" in resultado.relatorio


def test_minutos_zero_faz_um_scan(tmp_path):
    relogio = Relogio()

    resultado = monitorar(
        minutos=0,
        destino=tmp_path,
        scanner=ScannerFake([REDES]),
        dormir=relogio.dormir,
        relogio=relogio,
    )

    assert resultado.analise.n_scans == 1
    assert relogio.esperas == []


def test_scan_que_falha_nao_para_o_monitoramento(tmp_path):
    relogio = Relogio()

    resultado = monitorar(
        minutos=3,
        intervalo=60,
        destino=tmp_path,
        scanner=ScannerFake([REDES, None, REDES]),
        dormir=relogio.dormir,
        relogio=relogio,
    )

    assert resultado.analise.n_scans == 2


def test_ctrl_c_gera_relatorio_parcial(tmp_path):
    relogio = Relogio()

    def interromper(segundos):
        raise KeyboardInterrupt

    resultado = monitorar(
        minutos=30,
        destino=tmp_path,
        scanner=ScannerFake([REDES] * 10),
        dormir=interromper,
        relogio=relogio,
    )

    assert resultado.analise.n_scans == 1
    assert resultado.arquivo_txt.exists()


@pytest.fixture
def cli_isolada(monkeypatch, tmp_path):
    """Sem caffeinate, sem notificação real e com log numa pasta temporária."""
    notificacoes = []
    monkeypatch.setattr(
        "y_tools.wifi.__main__.setup_logger",
        partial(setup_logger, log_folder=tmp_path / "logs"),
    )
    monkeypatch.setattr("y_tools.wifi.__main__.manter_acordado", lambda: None)
    monkeypatch.setattr(
        "y_tools.wifi.__main__.notificar", lambda t, m: notificacoes.append((t, m))
    )
    return notificacoes


def test_cli(monkeypatch, tmp_path, cli_isolada):
    monkeypatch.setattr(
        "y_tools.wifi.__main__.Scanner", lambda usar_corewlan: ScannerFake([REDES])
    )

    codigo = main(["--minutos", "0", "--saida", str(tmp_path / "saida")])

    assert codigo == 0
    assert len(list((tmp_path / "saida").glob("wifi_relatorio_*.txt"))) == 1
    assert cli_isolada == [("Scan Wi-Fi terminou", "2.4 GHz: canal 1 | 5 GHz: bloco 36-48")]


def test_cli_sem_scans_retorna_erro(monkeypatch, tmp_path, cli_isolada):
    monkeypatch.setattr(
        "y_tools.wifi.__main__.Scanner", lambda usar_corewlan: ScannerFake([None])
    )

    codigo = main(["--minutos", "0", "--saida", str(tmp_path)])

    assert codigo == 1
    assert cli_isolada == []
