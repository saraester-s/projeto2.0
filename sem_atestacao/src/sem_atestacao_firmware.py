"""Medição de firmware no clone sem atestação: o hash muda, mas ninguém o confere."""

from __future__ import annotations

import hashlib
from pathlib import Path

FIRMWARE_PATH = (
    Path(__file__).resolve().parent
    / "sem_atestacao_publish_sensores_esp"
    / "sem_atestacao_publish_sensores_esp.ino"
)


def medir_firmware(source: str | bytes) -> bytes:
    dados = source.encode("utf-8") if isinstance(source, str) else source
    return hashlib.sha256(dados).digest()


def medir_arquivo_firmware(path: Path | None = None) -> bytes:
    return hashlib.sha256((path or FIRMWARE_PATH).read_bytes()).digest()
