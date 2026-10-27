"""Teste manual: altere o .ino ou passe um hash e veja se a atestação aceita.

Exemplos (na raiz do repositório):

  python src/teste_manual_hash.py
  python src/teste_manual_hash.py --hash 0000000000000000000000000000000000000000000000000000000000000001
  python src/teste_manual_hash.py --enviar
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.firmware import (
    FIRMWARE_HASH_ESPERADO_HEX,
    FIRMWARE_PATH,
    medir_arquivo_firmware,
    normalizar_firmware_hash,
    veredito_hash,
)

RELAY_URL = "http://127.0.0.1:5000/atestar"


def main() -> int:
    parser = argparse.ArgumentParser(description="Conferir hash enrolado vs hash apresentado")
    parser.add_argument(
        "--hash",
        help="Hash de 64 hex que você digitou à mão (senão usa o SHA-256 atual do .ino)",
    )
    parser.add_argument(
        "--enviar",
        action="store_true",
        help="POST no relay local (precisa estar rodando em :5000)",
    )
    args = parser.parse_args()

    medido = medir_arquivo_firmware()
    if args.hash:
        apresentado = normalizar_firmware_hash(args.hash)
        origem = "hash digitado"
    else:
        apresentado = medido
        origem = str(FIRMWARE_PATH)

    veredito = veredito_hash(apresentado)
    print(f"arquivo:     {FIRMWARE_PATH}")
    print(f"enrolado:    {FIRMWARE_HASH_ESPERADO_HEX}")
    print(f"arquivo agora: {medido.hex()}")
    print(f"apresentado ({origem}): {apresentado.hex()}")
    print(f"veredito local: {veredito}")
    if medido.hex() != FIRMWARE_HASH_ESPERADO_HEX:
        print("O .ino mudou em relação ao hash enrolado. Se você apresentar esse hash novo, será RECUSADO.")

    if not args.enviar:
        return 0 if veredito == "ACEITO" else 2

    corpo = json.dumps({
        "origem": "teste_manual",
        "temperature": 25.0,
        "humidity": 60.0,
        "status": True,
        "firmware_hash": apresentado.hex(),
    }).encode("utf-8")
    pedido = urllib.request.Request(
        RELAY_URL,
        data=corpo,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(pedido, timeout=30) as resp:
            print(f"relay HTTP {resp.status}: {resp.read().decode('utf-8')}")
            return 0
    except urllib.error.HTTPError as err:
        print(f"relay HTTP {err.code}: {err.read().decode('utf-8')}")
        return 2
    except OSError as err:
        print(f"relay inacessivel em {RELAY_URL}: {err}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
