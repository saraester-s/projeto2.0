import sys
from pathlib import Path

import pytest

CLONE_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = CLONE_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sem_atestacao_contract_logic import IoTContract


@pytest.fixture
def firmware_source() -> str:
    return (
        SRC_DIR
        / "sem_atestacao_publish_sensores_esp"
        / "sem_atestacao_publish_sensores_esp.ino"
    ).read_text(encoding="utf-8")


@pytest.fixture
def relay_source() -> str:
    return (SRC_DIR / "sem_atestacao_novo_servidor_relay.py").read_text(encoding="utf-8")


@pytest.fixture
def contract_source() -> str:
    return (SRC_DIR / "sem_atestacao_sensor.vy").read_text(encoding="utf-8")


@pytest.fixture
def mock_dataset():
    return [
        {
            "id": "leitura_ok",
            "temp": 25.4,
            "umid": 60.1,
            "hardware_ok": True,
            "expected_category": "ON_CHAIN",
            "expected_sub": "DHT11_OK",
            "expected_granularity": "RECORD_FULL",
            "expected_ttl": "KEEP_TIMESTAMP",
            "should_send": True,
        },
        {
            "id": "sensor_nan",
            "temp": float("nan"),
            "umid": 55.0,
            "hardware_ok": True,
            "expected_category": "OFF_CHAIN",
            "expected_sub": "DHT11_NAN",
            "expected_granularity": "SKIP_TX",
            "expected_ttl": "RETRY_2S",
            "should_send": False,
        },
        {
            "id": "temp_fora",
            "temp": 101.0,
            "umid": 40.0,
            "hardware_ok": True,
            "expected_category": "ON_CHAIN",
            "expected_sub": "FAIXA_TEMPERATURA",
            "expected_granularity": "FIELD_TEMP",
            "expected_ttl": "NO_WRITE_KEEP_AUTH",
            "should_send": True,
        },
        {
            "id": "umid_fora",
            "temp": 20.0,
            "umid": 150.0,
            "hardware_ok": True,
            "expected_category": "ON_CHAIN",
            "expected_sub": "FAIXA_UMIDADE",
            "expected_granularity": "FIELD_UMID",
            "expected_ttl": "NO_WRITE_KEEP_AUTH",
            "should_send": True,
        },
    ]


@pytest.fixture
def allowlist_dispositivos():
    return {
        "owner": "0xOWNER0000000000000000000000000000000001",
        "esp32": "0x316e45d3A5DF8AfE6091a746522db3b670874Ef6",
    }


@pytest.fixture
def contrato(allowlist_dispositivos):
    c = IoTContract(owner=allowlist_dispositivos["owner"], timestamp=1_700_000_000)
    c.autorizar_dispositivo(allowlist_dispositivos["owner"], allowlist_dispositivos["esp32"])
    return c
