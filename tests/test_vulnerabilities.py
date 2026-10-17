"""PoCs: estes testes PASSAM porque a vulnerabilidade está presente.

Quando o firmware/contrato forem corrigidos, inverta as asserções
(o ataque deve passar a falhar).
"""

from __future__ import annotations

import re

PRIVKEY_RE = re.compile(r'private_key\s*=\s*"0x[0-9a-fA-F]{64}"')
WIFI_PASS_RE = re.compile(r'password\s*=\s*"[^"]+"')
WALLET_RE = re.compile(r'minha_carteira\s*=\s*"(0x[0-9a-fA-F]{40})"')


def test_vuln_segredos_embutidos_no_firmware(firmware_source):
    """O .ino carrega chave EVM e senha Wi-Fi em texto claro.

    Qualquer pessoa com o fonte, um dump da flash ou o Git vê a identidade
    do ESP32 e pode assinar registrar_leitura no lugar da placa.
    """
    assert PRIVKEY_RE.search(firmware_source), (
        "Esperava chave privada hardcoded; se este assert falhar, o vazamento foi removido."
    )
    assert WIFI_PASS_RE.search(firmware_source)


def test_vuln_hardwareValido_e_autodeclarado(contrato, allowlist_dispositivos):
    """O contrato não atesta o sensor nem o firmware.

    sensor.vy grava _status exatamente como o msg.sender enviou.
    Um dispositivo autorizado (ou quem tiver a chave do publish_sensores_esp.ino)
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
    firmware_source,
    allowlist_dispositivos,
):
    """Encadeia as duas falhas: identidade no .ino + ausência de prova no contrato.

    O endereço minha_carteira é o da placa. Quem extrai a chave assina como
    esse endereço e polui o histórico daquele deviceId, não de um invasor novo.
    """
    match = WALLET_RE.search(firmware_source)
    assert match, "Carteira do ESP32 não encontrada no firmware"
    identidade_placa = match.group(1)

    assert identidade_placa.lower() == allowlist_dispositivos["esp32"].lower()

    contrato.registrar_leitura(identidade_placa, 99, 1, True)
    assert contrato.historico[identidade_placa][0].hardwareValido is True
    assert contrato.contagem_leituras[identidade_placa] == 1
