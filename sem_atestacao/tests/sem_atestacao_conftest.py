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
