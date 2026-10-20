"""PoCs do clone sem atestação de firmware."""

from __future__ import annotations

import re

PRIVKEY_RE = re.compile(r'PRIVATE_KEY\s*=\s*"0x[0-9a-fA-F]{64}"')
WIFI_PASS_RE = re.compile(r'password\s*=\s*"[^"]+"')
WALLET_RE = re.compile(r'WALLET_ADDRESS\s*=\s*"(0x[0-9a-fA-F]{40})"')


def test_vuln_segredos_embutidos_no_firmware(firmware_source, relay_source):
    assert WIFI_PASS_RE.search(firmware_source)
    assert not PRIVKEY_RE.search(firmware_source)
    assert PRIVKEY_RE.search(relay_source)


def test_vuln_hardwareValido_e_autodeclarado(contrato, allowlist_dispositivos):
    """Sem hash de firmware: o contrato grava só a leitura declarada pelo sender."""
    esp32 = allowlist_dispositivos["esp32"]
    temperatura_inventada = 42
    umidade_inventada = 7

    contrato.registrar_leitura(esp32, temperatura_inventada, umidade_inventada, True)

    gravado = contrato.historico[esp32][0]
    assert gravado.temperatura == temperatura_inventada
    assert gravado.umidade == umidade_inventada
    assert gravado.hardwareValido is True
    assert "firmwareHash" not in gravado.__dataclass_fields__


def test_vuln_identidade_do_esp32_permite_forjar_historico(
    contrato,
    relay_source,
    allowlist_dispositivos,
):
    match = WALLET_RE.search(relay_source)
    assert match, "Carteira do laboratório não encontrada no relay"
    identidade_placa = match.group(1)

    assert identidade_placa.lower() == allowlist_dispositivos["esp32"].lower()

    contrato.registrar_leitura(identidade_placa, 99, 1, True)
    assert contrato.historico[identidade_placa][0].hardwareValido is True
    assert contrato.contagem_leituras[identidade_placa] == 1
