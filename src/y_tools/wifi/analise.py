"""Análise de congestionamento: quantas redes vizinhas interferem em cada canal/bloco."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field

from .coleta import Rede

CANAIS_24 = (1, 6, 11)
"""Canais de 2.4 GHz que não se sobrepõem — os únicos que vale a pena escolher."""

BLOCOS_5 = {
    "36-48": range(36, 49),
    "52-64 (DFS)": range(52, 65),
    "100-112 (DFS)": range(100, 113),
    "116-128 (DFS)": range(116, 129),
    "132-144 (DFS)": range(132, 145),
    "149-161": range(149, 162),
}
"""Blocos de 80 MHz em 5 GHz. DFS pode ser derrubado por radar, então é evitado na sugestão."""

PROPRIO_DBM = -55
"""Sinal mais forte que isso = quase certamente o seu próprio roteador (fica de fora)."""

FORTE_DBM = -75
"""Vizinho com sinal mais forte que isso atrapalha de verdade."""


def centro_24(rede: Rede) -> int:
    """
    Canal central de uma rede de 2.4 GHz.

    * Em 40 MHz o canal informado é o primário; o secundário fica 4 canais acima
      (canais baixos) ou abaixo (altos), então o centro fica a 2 canais de distância.

    Args:
        rede: rede de 2.4 GHz.

    Returns:
        Número do canal central.
    """

    if rede.largura >= 40:
        return rede.canal + 2 if rede.canal <= 7 else rede.canal - 2
    return rede.canal


def interfere_24(rede: Rede, canal: int) -> bool:
    """
    Diz se uma rede de 2.4 GHz se sobrepõe a um canal de 20 MHz.

    Os canais são espaçados de 5 MHz e cada rede de 20 MHz ocupa ~22 MHz (±2
    canais), então dois canais a até 4 de distância já se sobrepõem.

    Args:
        rede: rede de 2.4 GHz.
        canal: canal candidato (1, 6 ou 11).

    Returns:
        `True` se houver sobreposição de espectro.
    """

    meia_largura = 4 if rede.largura >= 40 else 2
    return abs(centro_24(rede) - canal) <= 2 + meia_largura


def canais_ocupados_5(rede: Rede) -> range | list[int]:
    """
    Canais (números de 20 MHz) cobertos por uma rede de 5 GHz, conforme a largura.

    Args:
        rede: rede de 5 GHz.

    Returns:
        Números de canal cobertos.
    """

    c, w = rede.canal, rede.largura
    if w >= 160:
        base = 36 if c <= 64 else 100 if c <= 128 else 149
        return range(base, base + 29)
    if w == 80:
        for base in (36, 52, 100, 116, 132, 149):
            if base <= c < base + 16:
                return range(base, base + 13)
    if w == 40:
        base = c if (c - 36) % 8 == 0 or (c - 149) % 8 == 0 else c - 4
        return range(base, base + 5)
    return [c]


def interfere_5(rede: Rede, bloco: range) -> bool:
    """
    Diz se uma rede de 5 GHz ocupa algum canal do bloco.

    Args:
        rede: rede de 5 GHz.
        bloco: faixa de canais (um valor de `BLOCOS_5`).

    Returns:
        `True` se houver sobreposição.
    """

    return any(c in bloco for c in canais_ocupados_5(rede))


@dataclass(frozen=True)
class Congestionamento:
    """Média de redes vizinhas interferindo num canal ou bloco, por scan."""

    nome: str
    media: float
    fortes: float
    """Média só das vizinhas com sinal acima de `FORTE_DBM`."""


@dataclass
class Analise:
    """Acumula vários scans e calcula o congestionamento médio de cada canal/bloco."""

    proprio_dbm: int = PROPRIO_DBM
    forte_dbm: int = FORTE_DBM
    n_scans: int = 0
    soma: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    soma_fortes: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    proprias: set[tuple[str, int, int]] = field(default_factory=set)
    """Redes ignoradas por serem fortes demais: `(banda, canal, rssi)`."""

    def _forte(self, rede: Rede) -> bool:
        """`True` se a vizinha tem sinal acima de `forte_dbm`."""

        return rede.rssi is not None and rede.rssi > self.forte_dbm

    def _contar(self, chave: str, rede: Rede) -> None:
        """Soma uma vizinha interferindo em `chave`."""

        self.soma[chave] += 1
        if self._forte(rede):
            self.soma_fortes[chave] += 1

    def adicionar(self, redes: Iterable[Rede]) -> None:
        """
        Registra um scan.

        * Redes de 6 GHz não disputam espectro com 2.4/5 GHz e são ignoradas.

        Args:
            redes: redes vistas no scan.
        """

        self.n_scans += 1
        for rede in redes:
            if rede.rssi is not None and rede.rssi > self.proprio_dbm:
                self.proprias.add((rede.banda, rede.canal, rede.rssi))
                continue
            if rede.banda == "2.4":
                for canal in CANAIS_24:
                    if interfere_24(rede, canal):
                        self._contar(_chave_24(canal), rede)
            elif rede.banda == "5":
                for nome, bloco in BLOCOS_5.items():
                    if interfere_5(rede, bloco):
                        self._contar(nome, rede)

    def _media(self, chave: str, nome: str) -> Congestionamento:
        """Congestionamento médio de uma chave."""

        n = max(self.n_scans, 1)
        return Congestionamento(
            nome=nome, media=self.soma[chave] / n, fortes=self.soma_fortes[chave] / n
        )

    def canais_24(self) -> list[Congestionamento]:
        """
        Congestionamento médio dos canais 1, 6 e 11.

        Returns:
            Um item por canal, na ordem de `CANAIS_24`.
        """

        return [self._media(_chave_24(c), str(c)) for c in CANAIS_24]

    def blocos_5(self) -> list[Congestionamento]:
        """
        Congestionamento médio dos blocos de 80 MHz.

        Returns:
            Um item por bloco, na ordem de `BLOCOS_5`.
        """

        return [self._media(nome, nome) for nome in BLOCOS_5]

    def melhor_24(self) -> int:
        """
        Canal de 2.4 GHz menos congestionado (desempate pelo total de vizinhas).

        Returns:
            1, 6 ou 11.
        """

        melhor = min(self.canais_24(), key=lambda c: (c.fortes, c.media))
        return int(melhor.nome)

    def melhor_5(self, incluir_dfs: bool = False) -> str:
        """
        Bloco de 5 GHz menos congestionado.

        Args:
            incluir_dfs: `True` considera também os blocos DFS.

        Returns:
            Nome do bloco (chave de `BLOCOS_5`).
        """

        candidatos = [b for b in self.blocos_5() if incluir_dfs or "DFS" not in b.nome]
        return min(candidatos, key=lambda b: (b.fortes, b.media)).nome


def _chave_24(canal: int) -> str:
    """Chave interna de um canal de 2.4 GHz nos contadores."""

    return f"2.4 canal {canal}"


def formatar_relatorio(
    analise: Analise,
    metodo: str,
    minutos: float,
    rede_atual: Rede | None = None,
) -> str:
    """
    Monta o relatório em texto.

    Args:
        analise: scans acumulados.
        metodo: descrição do método de coleta.
        minutos: duração do monitoramento.
        rede_atual: rede em que o Mac está conectado, se conhecida.

    Returns:
        Relatório pronto para salvar ou exibir.
    """

    linhas = [
        f"Método: {metodo} | {analise.n_scans} scans em ~{minutos:.0f} min",
    ]
    if rede_atual is not None:
        sinal = f", sinal {rede_atual.rssi} dBm" if rede_atual.rssi is not None else ""
        linhas.append(
            f"Conectado em: canal {rede_atual.canal} ({rede_atual.banda} GHz, "
            f"{rede_atual.largura} MHz{sinal})"
        )

    linhas += ["", f"Ignoradas (provavelmente o SEU roteador, sinal > {analise.proprio_dbm} dBm):"]
    proprias = sorted(analise.proprias, key=lambda p: (p[0], p[1], p[2]))
    linhas.append(
        "  "
        + (", ".join(f"{b} GHz canal {c} ({s} dBm)" for b, c, s in proprias) or "nenhuma")
    )

    linhas += ["", "=== 2.4 GHz: média de redes vizinhas interferindo ==="]
    for c in analise.canais_24():
        linhas.append(f"Canal {c.nome:>2}: {c.media:5.1f}   (fortes: {c.fortes:.1f})")
    linhas.append(f"--> Melhor: canal {analise.melhor_24()}")

    linhas += ["", "=== 5 GHz: média de redes vizinhas por bloco de 80 MHz ==="]
    for b in analise.blocos_5():
        linhas.append(f"{b.nome:>14}: {b.media:5.1f}   (fortes: {b.fortes:.1f})")
    linhas.append(f"--> Melhor sem DFS: bloco {analise.melhor_5()}")

    if metodo.startswith("system_profiler"):
        linhas += [
            "",
            "! Sem sinal das vizinhas: a sugestão só conta redes, sem pesar a força.",
            "! Instale o extra `wifi` (pip install -e '.[wifi]') para usar o CoreWLAN.",
        ]

    return "\n".join(linhas)
