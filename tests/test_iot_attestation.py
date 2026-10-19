import pytest

from src.contract_logic import OutOfRange, UnauthorizedDevice
from src.firmware import (
    CHAIN_ID,
    CONTRACT_FUNCTION,
    build_transaction_payload,
    categorize_reading,
    pipeline_from_subcategory,
)


# 1. Categorização: rótulo principal NÃO basta — a subcategoria alimenta as etapas 3 e 4
def test_domain_categorization(mock_dataset):
    for item in mock_dataset:
        res = categorize_reading(item["temp"], item["umid"], item["hardware_ok"])
        assert res.category == item["expected_category"]
        assert res.subcategory == item["expected_sub"]
        assert res.should_send == item["should_send"]

        pipeline = pipeline_from_subcategory(res)
        assert pipeline["granularity"] == item["expected_granularity"]
        assert pipeline["ttl_policy"] == item["expected_ttl"]

    # Mesma categoria ON_CHAIN (camada do contrato), subcategorias diferentes:
    # FAIXA_TEMPERATURA → assert só de _temp (não revoga a placa)
    # FAIXA_UMIDADE     → assert só de _umid (não mistura com temperatura)
    temp_fora = categorize_reading(101.0, 40.0, True)
    umid_fora = categorize_reading(20.0, 150.0, True)
    assert temp_fora.category == "ON_CHAIN"
    assert umid_fora.category == "ON_CHAIN"
    assert temp_fora.category == umid_fora.category
    assert temp_fora.subcategory == "FAIXA_TEMPERATURA"
    assert umid_fora.subcategory == "FAIXA_UMIDADE"
    assert temp_fora.subcategory != umid_fora.subcategory
    assert pipeline_from_subcategory(temp_fora)["granularity"] == "FIELD_TEMP"
    assert pipeline_from_subcategory(umid_fora)["granularity"] == "FIELD_UMID"


# 2. Camada firmware vs contrato vs relay (HTTP no chip; EVM no PC; sensor.vy no desenho novo)
def test_mitigation_layer_routing(firmware_source, contract_source, relay_source):
    assert "HTTPClient.h" in firmware_source
    assert "/atestar" in firmware_source
    assert "isnan(temp) || isnan(umid)" in firmware_source
    assert "return;" in firmware_source
    assert "Web3 web3(" not in firmware_source
    assert "def registrar_leitura(_temp: uint256, _umid: uint256, _status: bool)" in contract_source
    assert 'encode_abi("registrar"' in relay_source
    assert "firmwareHash" in relay_source
    assert str(CHAIN_ID) in relay_source or "1075" in relay_source

    payload = build_transaction_payload(22.9, 48.2, True)
    assert payload.target_layer == "EVM_CONTRACT"
    assert payload.function_signature == CONTRACT_FUNCTION
    assert payload.chain_id == CHAIN_ID
    assert payload.temp == 22
    assert payload.umid == 48
    assert payload.status is True
    assert payload.value_wei == 0
    assert CONTRACT_FUNCTION in payload.rule_text

    with pytest.raises(ValueError, match="NaN"):
        build_transaction_payload(float("nan"), 50.0, True)


# 3. Granularidade do histórico (por endereço + índice, não mistura placas)
def test_granularity_purification(contrato, allowlist_dispositivos):
    esp32 = allowlist_dispositivos["esp32"]
    outra_placa = "0xDEVICE00000000000000000000000000000002"
    contrato.autorizar_dispositivo(allowlist_dispositivos["owner"], outra_placa)

    contrato.registrar_leitura(esp32, 25, 60, True)
    contrato.block_timestamp += 10
    contrato.registrar_leitura(esp32, 26, 61, True)
    contrato.registrar_leitura(outra_placa, 18, 40, False)

    assert contrato.contagem_leituras[esp32] == 2
    assert contrato.contagem_leituras[outra_placa] == 1
    assert contrato.historico[esp32][0].temperatura == 25
    assert contrato.historico[esp32][1].temperatura == 26
    assert contrato.historico[outra_placa][0].temperatura == 18
    assert contrato.historico[esp32][0].hardwareValido is True
    assert contrato.historico[outra_placa][0].hardwareValido is False


# 4. Timestamp da rede (imutável por registro; equivalente à política de TTL)
def test_rule_expiration_policy(contrato, allowlist_dispositivos):
    esp32 = allowlist_dispositivos["esp32"]

    contrato.block_timestamp = 1_700_000_000
    primeiro = contrato.registrar_leitura(esp32, 24, 55, True)

    contrato.block_timestamp = 1_700_000_000 + 86_400
    segundo = contrato.registrar_leitura(esp32, 27, 58, True)

    assert primeiro.timestamp == 1_700_000_000
    assert segundo.timestamp == 1_700_000_000 + 86_400
    assert contrato.historico[esp32][0].timestamp == primeiro.timestamp
    assert contrato.historico[esp32][1].timestamp != primeiro.timestamp


# 5. Dano colateral / allowlist (só dispositivos autorizados gravam)
def test_collateral_damage_rate(contrato, allowlist_dispositivos, mock_dataset):
    owner = allowlist_dispositivos["owner"]
    esp32 = allowlist_dispositivos["esp32"]
    invasor = "0xATTACKER000000000000000000000000000003"

    contrato.registrar_leitura(esp32, 25, 60, True)
    assert contrato.contagem_leituras[esp32] == 1

    with pytest.raises(UnauthorizedDevice):
        contrato.registrar_leitura(invasor, 25, 60, True)

    with pytest.raises(OutOfRange, match="Temperatura"):
        contrato.registrar_leitura(esp32, 101, 40, True)

    with pytest.raises(OutOfRange, match="Umidade"):
        contrato.registrar_leitura(esp32, 20, 150, True)

    contrato.revogar_dispositivo(owner, esp32)
    with pytest.raises(UnauthorizedDevice):
        contrato.registrar_leitura(esp32, 25, 60, True)

    assert contrato.historico[esp32][0].temperatura == 25
    assert invasor not in contrato.historico

    enviaveis_ok = [
        item
        for item in mock_dataset
        if item["expected_sub"] == "DHT11_OK"
    ]
    assert len(enviaveis_ok) == 1
