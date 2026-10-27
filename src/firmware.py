"""Medição e allowlist do hash de firmware (clone com atestação)."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

FIRMWARE_PATH = Path(__file__).resolve().parent / "publish_sensores_esp" / "publish_sensores_esp.ino"
_HASH_CONST_RE = re.compile(rb'const char\* firmwareHash = "[0-9a-fA-F]{64}";')
_HASH_CANON = b'const char* firmwareHash = "' + b"0" * 64 + b'";'


def _canonico(dados: bytes) -> bytes:
    """Zera o campo firmwareHash para o hash do arquivo não depender do próprio valor."""
    if _HASH_CONST_RE.search(dados):
        return _HASH_CONST_RE.sub(_HASH_CANON, dados, count=1)
    return dados


def medir_firmware(source: str | bytes) -> bytes:
    dados = source.encode("utf-8") if isinstance(source, str) else source
    return hashlib.sha256(_canonico(dados)).digest()


def medir_arquivo_firmware(path: Path | None = None) -> bytes:
    return medir_firmware((path or FIRMWARE_PATH).read_bytes())


FIRMWARE_HASH_ESPERADO_HEX = (
    "8422ebe782c2f51ab17c330621d0b4c2c29db4175a82929fec0bab04d2ba28b6"
)
FIRMWARE_HASH_ESPERADO = bytes.fromhex(FIRMWARE_HASH_ESPERADO_HEX)


def hash_esta_enrolado(digest: bytes, esperado: bytes | None = None) -> bool:
    alvo = FIRMWARE_HASH_ESPERADO if esperado is None else esperado
    return digest == alvo


def normalizar_firmware_hash(valor: str) -> bytes:
    texto = valor.strip()
    if texto.startswith(("0x", "0X")):
        texto = texto[2:]
    return bytes.fromhex(texto)


def veredito_hash(digest: bytes, esperado: bytes | None = None) -> str:
    return "ACEITO" if hash_esta_enrolado(digest, esperado) else "RECUSADO"
