"""PoCs: estes testes PASSAM porque a vulnerabilidade está presente.

Quando o firmware/contrato forem corrigidos, inverta as asserções
(o ataque deve passar a falhar).
"""

from __future__ import annotations

import re

PRIVKEY_RE = re.compile(r'PRIVATE_KEY\s*=\s*"0x[0-9a-fA-F]{64}"')
WIFI_PASS_RE = re.compile(r'password\s*=\s*"[^"]+"')
WALLET_RE = re.compile(r'WALLET_ADDRESS\s*=\s*"(0x[0-9a-fA-F]{40})"')


def test_vuln_segredos_embutidos_no_firmware(firmware_source, relay_source):
    """A senha Wi-Fi ficou no .ino; a chave EVM saiu do chip e foi para o relay.

    Quem lê o Git ainda assina atestações como a carteira do laboratório, só que
    agora pelo PC, não pelo ESP32.
    """
    assert WIFI_PASS_RE.search(firmware_source)
    assert not PRIVKEY_RE.search(firmware_source)
    assert PRIVKEY_RE.search(relay_source), (
        "Esperava chave privada no relay; se este assert falhar, o vazamento foi removido."
    )


def test_vuln_hardwareValido_e_autodeclarado(contrato, allowlist_dispositivos):
    """O contrato não atesta o sensor nem o firmware.

    sensor.vy grava _status exatamente como o msg.sender enviou.
    Um dispositivo autorizado (ou quem tiver a chave do relay)
    forja temperatura/umidade e marca hardwareValido=True sem DHT11.
    """
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
    """Encadeia as duas falhas: identidade no relay + ausência de prova no contrato.

    WALLET_ADDRESS é quem assina na testnet. Quem extrai a chave do relay polui
    o histórico daquele endereço, não o de um invasor novo.
    """
    match = WALLET_RE.search(relay_source)
    assert match, "Carteira do laboratório não encontrada no relay"
    identidade_placa = match.group(1)

    assert identidade_placa.lower() == allowlist_dispositivos["esp32"].lower()

    contrato.registrar_leitura(identidade_placa, 99, 1, True)
    assert contrato.historico[identidade_placa][0].hardwareValido is True
    assert contrato.contagem_leituras[identidade_placa] == 1
