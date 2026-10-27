from sem_atestacao_firmware import medir_firmware


def test_firmware_alterado_ainda_e_aceito(contrato, allowlist_dispositivos, firmware_source):
    """Sem allowlist de hash: o código muda, o hash muda, a leitura mesmo assim grava."""
    esp32 = allowlist_dispositivos["esp32"]

    hash_original = medir_firmware(firmware_source)
    hash_alterado = medir_firmware(firmware_source + "\n// trecho extra: firmware nao enrolado\n")
    assert hash_original != hash_alterado
    assert "firmware_hash" not in firmware_source

    contrato.registrar_leitura(esp32, 25, 60, True)
    contrato.registrar_leitura(esp32, 26, 61, True)

    assert contrato.contagem_leituras[esp32] == 2
    assert contrato.historico[esp32][0].temperatura == 25
    assert contrato.historico[esp32][1].temperatura == 26
    assert not hasattr(contrato, "firmware_esperado")
