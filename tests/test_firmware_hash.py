import pytest

from src.contract_logic import UnknownFirmware
from src.firmware import (
    FIRMWARE_HASH_ESPERADO,
    hash_esta_enrolado,
    medir_arquivo_firmware,
    medir_firmware,
    veredito_hash,
)


def test_firmware_alterado_nao_e_aceito(contrato, allowlist_dispositivos, firmware_source):
    owner = allowlist_dispositivos["owner"]
    esp32 = allowlist_dispositivos["esp32"]

    hash_enrolado = medir_arquivo_firmware()
    assert hash_enrolado == FIRMWARE_HASH_ESPERADO
    assert hash_esta_enrolado(hash_enrolado)
    assert veredito_hash(hash_enrolado) == "ACEITO"
    assert "/atestar" in firmware_source
    assert "firmware_hash" in firmware_source
    assert ":5001/leitura" not in firmware_source

    hash_alterado = medir_firmware(firmware_source + "\n// trecho extra: firmware nao enrolado\n")
    assert hash_alterado != hash_enrolado
    assert not hash_esta_enrolado(hash_alterado)
    assert veredito_hash(hash_alterado) == "RECUSADO"

    contrato.definir_firmware_esperado(owner, hash_enrolado)
    aceito = contrato.registrar_atestacao(esp32, hash_enrolado, True)
    assert aceito == hash_enrolado
    assert contrato.contagem_atestacoes[esp32] == 1

    with pytest.raises(UnknownFirmware, match="nao autorizado"):
        contrato.registrar_atestacao(esp32, hash_alterado, True)

    assert contrato.contagem_atestacoes[esp32] == 1
    assert contrato.atestacoes[esp32][0] == hash_enrolado
