"""Modelo testável das regras de classificação (NaN off-chain, faixa on-chain).

Clone sem atestação de firmware: o sketch envia só temperatura/umidade ao relay.
Não há firmware_hash. O payload on-chain é registrar_leitura.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

CHAIN_ID = 1076
CONTRACT_FUNCTION = "registrar_leitura(uint256,uint256,bool)"
GAS_LIMIT = 3_000_000
VALUE_WEI = 0
DHT_PIN = 4
SEND_INTERVAL_MS = 10_000
TEMP_MAX = 100
UMID_MAX = 100


@dataclass(frozen=True)
class LeituraClassificada:
    """category = camada de ação; subcategory = granularidade e duração da regra."""

    category: str
    subcategory: str
    should_send: bool
    temp_uint: int | None
    umid_uint: int | None
    hardware_valido: bool
    granularity: str
    ttl_policy: str


@dataclass(frozen=True)
class PayloadTransacao:
    target_layer: str
    function_signature: str
    rule_text: str
    chain_id: int
    temp: int
    umid: int
    status: bool
    gas_limit: int
    value_wei: int


def _is_nan(value: float | None) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def classify_reading(
    temp: float | None,
    umid: float | None,
    hardware_ok: bool = True,
) -> LeituraClassificada:
    """Classifica a leitura do ESP32.

    category (camada): OFF_CHAIN age no firmware; ON_CHAIN age no contrato.
    Não há ramo de atestação de firmware.
    """
    if _is_nan(temp) or _is_nan(umid):
        return LeituraClassificada(
            category="OFF_CHAIN",
            subcategory="DHT11_NAN",
            should_send=False,
            temp_uint=None,
            umid_uint=None,
            hardware_valido=False,
            granularity="SKIP_TX",
            ttl_policy="RETRY_2S",
        )

    temp_uint = int(temp) & 0xFFFFFFFF
    umid_uint = int(umid) & 0xFFFFFFFF

    if temp_uint > TEMP_MAX:
        return LeituraClassificada(
            category="ON_CHAIN",
            subcategory="FAIXA_TEMPERATURA",
            should_send=True,
            temp_uint=temp_uint,
            umid_uint=umid_uint,
            hardware_valido=hardware_ok,
            granularity="FIELD_TEMP",
            ttl_policy="NO_WRITE_KEEP_AUTH",
        )
    if umid_uint > UMID_MAX:
        return LeituraClassificada(
            category="ON_CHAIN",
            subcategory="FAIXA_UMIDADE",
            should_send=True,
            temp_uint=temp_uint,
            umid_uint=umid_uint,
            hardware_valido=hardware_ok,
            granularity="FIELD_UMID",
            ttl_policy="NO_WRITE_KEEP_AUTH",
        )
    if not hardware_ok:
        return LeituraClassificada(
            category="ON_CHAIN",
            subcategory="HARDWARE_INVALID",
            should_send=True,
            temp_uint=temp_uint,
            umid_uint=umid_uint,
            hardware_valido=False,
            granularity="RECORD_STATUS",
            ttl_policy="KEEP_TIMESTAMP",
        )
    return LeituraClassificada(
        category="ON_CHAIN",
        subcategory="DHT11_OK",
        should_send=True,
        temp_uint=temp_uint,
        umid_uint=umid_uint,
        hardware_valido=True,
        granularity="RECORD_FULL",
        ttl_policy="KEEP_TIMESTAMP",
    )


def categorize_reading(
    temp: float | None,
    umid: float | None,
    hardware_ok: bool = True,
) -> LeituraClassificada:
    return classify_reading(temp, umid, hardware_ok)


def pipeline_from_subcategory(res: LeituraClassificada) -> dict[str, str]:
    if not res.subcategory:
        raise ValueError("Classificador incompleto: falta subcategory")
    return {
        "layer": res.category,
        "granularity": res.granularity,
        "ttl_policy": res.ttl_policy,
    }


def build_transaction_payload(temp: float, umid: float, hardware_ok: bool) -> PayloadTransacao:
    leitura = classify_reading(temp, umid, hardware_ok)
    if not leitura.should_send:
        raise ValueError("Firmware não envia transação quando o DHT11 retorna NaN")

    signature = CONTRACT_FUNCTION
    return PayloadTransacao(
        target_layer="EVM_CONTRACT",
        function_signature=signature,
        rule_text=f"{signature}:{leitura.temp_uint}:{leitura.umid_uint}:{leitura.hardware_valido}",
        chain_id=CHAIN_ID,
        temp=leitura.temp_uint,
        umid=leitura.umid_uint,
        status=leitura.hardware_valido,
        gas_limit=GAS_LIMIT,
        value_wei=VALUE_WEI,
    )
