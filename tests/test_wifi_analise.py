import pytest

from y_tools.wifi import (
    METODO_PROFILER,
    Analise,
    Rede,
    canais_ocupados_5,
    formatar_relatorio,
    interfere_24,
    juntar,
    parsear_meus_canais,
)


def r24(canal, largura=20, rssi=-80):
    return Rede(canal=canal, largura=largura, banda="2.4", rssi=rssi)


def r5(canal, largura=80, rssi=-80):
    return Rede(canal=canal, largura=largura, banda="5", rssi=rssi)


@pytest.mark.parametrize(
    "rede, alvo, esperado",
    [
        (r24(1), 1, True),
        (r24(5), 1, True),  # canal 5 fica em cima do 1 e do 6
        (r24(5), 6, True),
        (r24(6), 1, False),
        (r24(11), 6, False),
        (r24(1, largura=40), 6, True),  # 40 MHz no 1 vai até o 7
        (r24(11, largura=40), 1, False),
    ],
)
def test_interfere_24(rede, alvo, esperado):
    assert interfere_24(rede, alvo) is esperado


@pytest.mark.parametrize(
    "rede, esperado",
    [
        (r5(36, 20), [36]),
        (r5(40, 40), range(36, 41)),
        (r5(44, 80), range(36, 49)),
        (r5(40, 160), range(36, 65)),
        (r5(157, 80), range(149, 162)),
    ],
)
def test_canais_ocupados_5(rede, esperado):
    assert list(canais_ocupados_5(rede)) == list(esperado)


def test_ignora_o_proprio_roteador():
    analise = Analise()
    analise.adicionar([r24(11, rssi=-40), r5(36, rssi=-41)])

    assert analise.proprias == {("2.4", 11, -40), ("5", 36, -41)}
    assert all(c.media == 0 for c in analise.canais_24() + analise.blocos_5())


def test_160mhz_conta_em_dois_blocos():
    analise = Analise()
    analise.adicionar([r5(40, 160)])

    medias = {b.nome: b.media for b in analise.blocos_5()}
    assert medias["36-48"] == 1
    assert medias["52-64 (DFS)"] == 1
    assert medias["149-161"] == 0


def test_ignora_6ghz():
    analise = Analise()
    analise.adicionar([Rede(canal=37, largura=160, banda="6", rssi=-60)])

    assert all(b.media == 0 for b in analise.blocos_5())


def test_media_por_scan_e_fortes():
    analise = Analise()
    analise.adicionar([r24(1, rssi=-70), r24(11, rssi=-85)])
    analise.adicionar([r24(1, rssi=-90)])

    canais = {int(c.nome): c for c in analise.canais_24()}
    assert analise.n_scans == 2
    assert canais[1].media == 1.0
    assert canais[1].fortes == 0.5
    assert canais[11].media == 0.5
    assert canais[11].fortes == 0.0


def test_melhor_prioriza_vizinhos_fortes():
    analise = Analise()
    # * canal 1 tem mais redes, mas todas fracas; o 11 tem uma forte
    analise.adicionar([r24(1, rssi=-88), r24(1, rssi=-88), r24(6, rssi=-70), r24(11, rssi=-70)])

    assert analise.melhores_24() == [1]
    assert analise.melhor_24() == 1


def test_melhor_5_evita_dfs_por_padrao():
    analise = Analise()
    analise.adicionar([r5(36), r5(149)])

    assert analise.melhores_5() == ["36-48", "149-161"]
    assert analise.melhor_5() == "36-48"
    assert all("DFS" in b for b in analise.melhores_5(incluir_dfs=True))


def test_empate_desfeito_pelo_total():
    analise = Analise()
    # * mesma quantidade de fortes (zero), mas o 36-48 tem mais redes fracas
    analise.adicionar([r5(36), r5(36), r5(149)])

    assert analise.melhores_5() == ["149-161"]


@pytest.mark.parametrize(
    "itens, conector, esperado",
    [
        ([], "e", ""),
        ([11], "e", "11"),
        ([1, 11], "ou", "1 ou 11"),
        ([1, 6, 11], "e", "1, 6 e 11"),
    ],
)
def test_juntar(itens, conector, esperado):
    assert juntar(itens, conector) == esperado


def test_sem_scans_nao_divide_por_zero():
    assert Analise().canais_24()[0].media == 0


def test_formatar_relatorio():
    analise = Analise()
    analise.adicionar([r24(6), r5(36), r24(11, rssi=-40)])

    texto = formatar_relatorio(
        analise, METODO_PROFILER, 30, rede_atual=r5(36, rssi=-41)
    )

    assert "1 scans em ~30 min" in texto
    assert "Conectado em: canal 36 (5 GHz, 80 MHz, sinal -41 dBm)" in texto
    assert "2.4 GHz canal 11 (-40 dBm)" in texto
    # * só o canal 6 tem vizinha: 1 e 11 empatam; no 5 GHz o 36-48 está ocupado
    assert "--> Empate: canais 1 e 11 (qualquer um serve)" in texto
    assert "--> Melhor sem DFS: bloco 149-161" in texto
    assert "extra `wifi`" in texto


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("", set()),
        ("2.4:11,5:149", {("2.4", 11), ("5", 149)}),
        (" 2.4GHz:1 , 5ghz:36 ", {("2.4", 1), ("5", 36)}),
        ("2:6", {("2.4", 6)}),
        ("11,149", {("2.4", 11), ("5", 149)}),
    ],
)
def test_parsear_meus_canais(texto, esperado):
    assert parsear_meus_canais(texto) == esperado


@pytest.mark.parametrize("texto", ["2.4:onze", "7:11", "5:"])
def test_parsear_meus_canais_invalido(texto):
    with pytest.raises(ValueError, match="inválido"):
        parsear_meus_canais(texto)


def test_canal_conhecido_so_ignora_a_rede_forte_nele():
    analise = Analise(meus_canais={("2.4", 11)})
    analise.adicionar(
        [
            r24(11, rssi=-39),  # o roteador
            r24(11, rssi=-80),  # vizinho fraco no mesmo canal: conta
            r24(1, rssi=-48),  # vizinho forte em outro canal: conta
        ]
    )

    canais = {int(c.nome): c for c in analise.canais_24()}
    assert analise.proprias == {("2.4", 11, -39)}
    assert canais[11].media == 1
    assert canais[1].media == 1
    assert canais[1].fortes == 1


def test_banda_sem_canal_conhecido_usa_o_limite():
    analise = Analise(meus_canais={("5", 149)})
    analise.adicionar([r24(1, rssi=-48), r5(36, rssi=-48)])

    assert analise.bandas_sem_canal() == ["2.4"]
    assert analise.proprias == {("2.4", 1, -48)}
    assert {b.nome: b.media for b in analise.blocos_5()}["36-48"] == 1


def test_relatorio_agrupa_sinais_e_avisa_banda_sem_canal():
    analise = Analise(meus_canais={("5", 149)})
    analise.adicionar([r5(149, rssi=-45)])
    analise.adicionar([r5(149, rssi=-37)])

    texto = formatar_relatorio(analise, "fake", 1)

    assert "Canais do seu roteador: 5 GHz canal 149" in texto
    assert "--> Empate sem DFS: blocos 36-48 e 149-161 (qualquer um serve)" in texto
    assert "5 GHz canal 149 (-45 a -37 dBm)" in texto
    assert "2.4 GHz sem canal conhecido" in texto
    assert "5 GHz sem canal conhecido" not in texto
