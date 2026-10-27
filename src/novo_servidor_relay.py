from collections import deque
from datetime import datetime, timezone
from pathlib import Path
import csv
import math
import re
import socket
import sys
import threading
import time

from flask import Flask, request, jsonify, render_template_string
from web3 import Web3

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.firmware import FIRMWARE_HASH_ESPERADO, hash_esta_enrolado

app = Flask(__name__)

RPC_URLS = (
    "https://json-rpc.evm.testnet.iota.cafe",
    "https://json-rpc.evm.testnet.iotaledger.net",
)

w3 = None
for rpc_url in RPC_URLS:
    candidato = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 20}))
    if candidato.is_connected():
        w3 = candidato
        break
if w3 is None:
    raise ConnectionError("Nao foi possivel conectar ao RPC da IOTA EVM Testnet")

CHAIN_ID = w3.eth.chain_id

PRIVATE_KEY = "0x547192f8e00d5f5e123539f1e8397cabb81dd7b1ff5b19b7e128187063423ba3"
WALLET_ADDRESS = "0x316e45d3A5DF8AfE6091a746522db3b670874Ef6"
CONTRACT_ADDRESS = "0xDAc95e767da4376456b132F4b78e18C0b8d0C669"

CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "firmwareHash", "type": "bytes32"},
            {"internalType": "bool", "name": "status", "type": "bool"}
        ],
        "name": "registrar",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)

historico = deque(maxlen=100)
_csv_lock = threading.RLock()
_lote_atual = []
_hardware_pronto = False
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_TX = DATA_DIR / "performance_atestacoes.csv"
CSV_RESUMO = DATA_DIR / "performance_resumo.csv"
CSV_MEDIA_TOTAL = DATA_DIR / "performance_media_total.csv"
CSV_MEDIA_TOTAL_CAMPOS = [
    "quando",
    "amostras",
    "tempo_medio_envio_ms",
    "tempo_medio_confirmacao_ms",
    "custo_medio_iota",
    "custo_medio_wei",
    "custo_total_iota",
    "custo_total_wei",
]
TAMANHO_LOTE = 30
CSV_RESUMO_CAMPOS = [
    "lote",
    "quando",
    "amostras",
    "tempo_medio_envio_ms",
    "tempo_medio_confirmacao_ms",
    "custo_medio_iota",
    "custo_medio_wei",
    "custo_total_iota",
    "custo_total_wei",
]
CSV_CAMPOS = [
    "quando",
    "status",
    "tx_hash",
    "tempo_envio_ms",
    "tempo_confirmacao_ms",
    "gas_price_wei",
    "gas_usado",
    "custo_wei",
    "custo_iota",
    "temperature",
    "humidity",
    "mensagem",
]

PAGINA_ATESTAR = """
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="5">
  <title>Atestações IoT</title>
  <style>
    body { font-family: Segoe UI, sans-serif; margin: 2rem; background: #111; color: #eee; }
    a { color: #8ecfff; }
    .ok { color: #7dffa3; }
    .err { color: #ff8a8a; }
    article { border: 1px solid #333; padding: 1rem; margin-bottom: 1rem; border-radius: 8px; }
    code { word-break: break-all; }
  </style>
</head>
<body>
  <h1>Relay de atestação</h1>
  <p>Esta página atualiza sozinha a cada 5s. O ESP32 deve fazer POST neste mesmo caminho.</p>
  <p>Eventos recebidos: <strong>{{ total }}</strong></p>
  {% if not hardware_pronto %}
    <article>
      <p class="err"><strong>Aguardando o hardware.</strong> A contagem do lote 30 só começa na primeira leitura válida do DHT11 (temperatura e umidade numéricas).</p>
    </article>
  {% endif %}
  {% if resumo %}
    <article>
      <p><strong>Desempenho</strong> — lote de {{ resumo.tamanho_lote }} envios reais do ESP32</p>
      <p>Progresso do lote atual: <strong>{{ resumo.envios_no_lote }}/{{ resumo.tamanho_lote }}</strong>
         (faltam {{ resumo.faltam }} | lotes fechados: {{ resumo.lotes_completos }})</p>
      {% if resumo.media_pronta %}
        <p>Média do lote {{ resumo.lote }} (atualizada após {{ resumo.tamanho_lote }} envios):</p>
        <p>Tempo médio até envio: {{ resumo.tempo_medio_envio_ms }} ms</p>
        <p>Tempo médio até registro on-chain: {{ resumo.tempo_medio_confirmacao_ms }} ms</p>
        <p>Custo médio: {{ resumo.custo_medio_iota }} IOTA ({{ resumo.custo_medio_wei }} wei)</p>
        <p>Custo total do lote: {{ resumo.custo_total_iota }} IOTA</p>
      {% else %}
        <p>A média só é gravada quando o lote de {{ resumo.tamanho_lote }} envios confirmados completar.</p>
      {% endif %}
      {% if media_total and media_total.amostras %}
        <p><strong>Média total</strong> ({{ media_total.amostras }} envios reais):</p>
        <p>Tempo médio de envio: {{ media_total.tempo_medio_envio_ms }} ms</p>
        <p>Tempo médio de confirmação: {{ media_total.tempo_medio_confirmacao_ms }} ms</p>
        <p>Custo médio: {{ media_total.custo_medio_iota }} IOTA | custo total: {{ media_total.custo_total_iota }} IOTA</p>
      {% endif %}
      <p>CSV: <code>{{ csv_tx }}</code>, <code>{{ csv_resumo }}</code>, <code>{{ csv_media_total }}</code></p>
    </article>
  {% endif %}
  {% if not eventos %}
    <p>Aguardando hardware... ligue o ESP32 na mesma Wi-Fi e aponte o firmware para
       <code>http://{{ lan_ip }}:5000/atestar</code> (127.0.0.1 no ESP é o próprio chip, não este PC).</p>
  {% endif %}
  {% for ev in eventos %}
    <article>
      <p><strong>{{ ev.quando }}</strong> —
         <span class="{{ 'ok' if ev.ok else 'err' }}">{{ ev.status }}</span></p>
      <p>Temp: {{ ev.temperature }} °C | Umid: {{ ev.humidity }} % | HW status: {{ ev.hw_status }}</p>
      <p>Firmware hash: <code>{{ ev.firmware_hash }}</code></p>
      {% if ev.tx_hash %}
        <p>TX: <code>{{ ev.tx_hash }}</code></p>
      {% endif %}
      {% if ev.tempo_confirmacao_ms %}
        <p>Tempo registro: {{ ev.tempo_confirmacao_ms }} ms | Custo: {{ ev.custo_iota }} IOTA</p>
      {% endif %}
      {% if ev.message %}
        <p>{{ ev.message }}</p>
      {% endif %}
    </article>
  {% endfor %}
</body>
</html>
"""


def _lan_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except OSError:
        return "IP_DA_MAQUINA"


def _normalizar_hash(firmware_hash_hex):
    if firmware_hash_hex is None:
        return None
    valor = str(firmware_hash_hex).strip()
    if valor.startswith("0x") or valor.startswith("0X"):
        valor = valor[2:]
    hex_only = re.sub(r"[^0-9a-fA-F]", "", valor)
    if len(hex_only) == 64:
        return bytes.fromhex(hex_only)
    return None


def _registrar_evento(**kwargs):
    evento = {
        "quando": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
        "ok": False,
        "status": "error",
        "temperature": None,
        "humidity": None,
        "hw_status": None,
        "firmware_hash": None,
        "tx_hash": None,
        "message": None,
    }
    evento.update(kwargs)
    historico.appendleft(evento)
    return evento


def _garantir_csv():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_TX.exists():
        with CSV_TX.open("w", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, fieldnames=CSV_CAMPOS).writeheader()
    header_resumo_ok = False
    if CSV_RESUMO.exists():
        primeira = CSV_RESUMO.read_text(encoding="utf-8").splitlines()
        header_resumo_ok = bool(primeira) and primeira[0].startswith("lote,")
    if not header_resumo_ok:
        with CSV_RESUMO.open("w", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, fieldnames=CSV_RESUMO_CAMPOS).writeheader()


def _append_csv(row):
    _garantir_csv()
    with _csv_lock:
        with CSV_TX.open("a", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, fieldnames=CSV_CAMPOS).writerow(row)
        if row.get("status") == "success" and _leitura_hardware_valida(row.get("temperature"), row.get("humidity")):
            _lote_atual.append(row)
            _gravar_media_total()
            if len(_lote_atual) == TAMANHO_LOTE:
                _gravar_media_lote(list(_lote_atual))
                _lote_atual.clear()


def _linhas_csv():
    _garantir_csv()
    with _csv_lock:
        with CSV_TX.open("r", newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))


def _leitura_hardware_valida(temperatura, umidade):
    temp = _to_float(temperatura)
    umid = _to_float(umidade)
    if temp is None or umid is None:
        return False
    if math.isnan(temp) or math.isnan(umid):
        return False
    if not (-20.0 <= temp <= 80.0):
        return False
    if not (0.0 <= umid <= 100.0):
        return False
    return True


def _marcar_hardware_pronto():
    global _hardware_pronto
    if not _hardware_pronto:
        _hardware_pronto = True
        print("[HARDWARE] DHT11 inicializado. Contagem do lote 30 iniciada.", flush=True)


def _to_float(valor):
    try:
        if valor is None or valor == "":
            return None
        return float(valor)
    except (TypeError, ValueError):
        return None


def _media_do_lote(confirmadas):
    tempos_envio = [v for v in (_to_float(l.get("tempo_envio_ms")) for l in confirmadas) if v is not None]
    tempos_conf = [v for v in (_to_float(l.get("tempo_confirmacao_ms")) for l in confirmadas) if v is not None]
    custos_wei = [v for v in (_to_float(l.get("custo_wei")) for l in confirmadas) if v is not None]
    custos_iota = [v for v in (_to_float(l.get("custo_iota")) for l in confirmadas) if v is not None]
    n = len(confirmadas)

    def media(valores):
        return round(sum(valores) / len(valores), 6) if valores else 0

    return {
        "amostras": n,
        "tempo_medio_envio_ms": round(media(tempos_envio), 2),
        "tempo_medio_confirmacao_ms": round(media(tempos_conf), 2),
        "custo_medio_wei": int(media(custos_wei)) if custos_wei else 0,
        "custo_medio_iota": media(custos_iota),
        "custo_total_wei": int(sum(custos_wei)) if custos_wei else 0,
        "custo_total_iota": round(sum(custos_iota), 12) if custos_iota else 0,
    }


def _envios_reais():
    return [
        linha for linha in _linhas_csv()
        if linha.get("status") == "success"
        and _leitura_hardware_valida(linha.get("temperature"), linha.get("humidity"))
        and _to_float(linha.get("tempo_envio_ms")) is not None
    ]


def _ler_media_total():
    _garantir_csv()
    if not CSV_MEDIA_TOTAL.exists():
        return None
    with CSV_MEDIA_TOTAL.open("r", newline="", encoding="utf-8") as fh:
        linhas = list(csv.DictReader(fh))
    if not linhas:
        return None
    ultima = linhas[-1]
    return {
        "quando": ultima.get("quando"),
        "amostras": _to_float(ultima.get("amostras")),
        "tempo_medio_envio_ms": _to_float(ultima.get("tempo_medio_envio_ms")),
        "tempo_medio_confirmacao_ms": _to_float(ultima.get("tempo_medio_confirmacao_ms")),
        "custo_medio_iota": _to_float(ultima.get("custo_medio_iota")),
        "custo_medio_wei": _to_float(ultima.get("custo_medio_wei")),
        "custo_total_iota": _to_float(ultima.get("custo_total_iota")),
        "custo_total_wei": _to_float(ultima.get("custo_total_wei")),
    }


def _gravar_media_total():
    reais = _envios_reais()
    if not reais:
        return
    media = _media_do_lote(reais)
    linha = {
        "quando": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
        "amostras": media["amostras"],
        "tempo_medio_envio_ms": media["tempo_medio_envio_ms"],
        "tempo_medio_confirmacao_ms": media["tempo_medio_confirmacao_ms"],
        "custo_medio_iota": media["custo_medio_iota"],
        "custo_medio_wei": media["custo_medio_wei"],
        "custo_total_iota": media["custo_total_iota"],
        "custo_total_wei": media["custo_total_wei"],
    }
    with CSV_MEDIA_TOTAL.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_MEDIA_TOTAL_CAMPOS)
        writer.writeheader()
        writer.writerow(linha)
    print(
        f"[MEDIA TOTAL] n={media['amostras']} | envio={media['tempo_medio_envio_ms']} ms | "
        f"custo_medio={media['custo_medio_iota']} IOTA",
        flush=True,
    )


def _lotes_salvos():
    _garantir_csv()
    with CSV_RESUMO.open("r", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _calcular_resumo(linhas=None):
    del linhas
    with _csv_lock:
        envios_no_lote = len(_lote_atual)
        lotes = _lotes_salvos()
    lotes_completos = len(lotes)
    ultimo = lotes[-1] if lotes else None
    resumo = {
        "tamanho_lote": TAMANHO_LOTE,
        "envios_no_lote": envios_no_lote,
        "faltam": TAMANHO_LOTE - envios_no_lote,
        "lotes_completos": lotes_completos,
        "media_pronta": ultimo is not None,
        "lote": int(ultimo["lote"]) if ultimo else 0,
    }
    if not ultimo:
        return resumo
    resumo.update({
        "amostras": _to_float(ultimo.get("amostras")),
        "tempo_medio_envio_ms": _to_float(ultimo.get("tempo_medio_envio_ms")),
        "tempo_medio_confirmacao_ms": _to_float(ultimo.get("tempo_medio_confirmacao_ms")),
        "custo_medio_wei": _to_float(ultimo.get("custo_medio_wei")),
        "custo_medio_iota": _to_float(ultimo.get("custo_medio_iota")),
        "custo_total_wei": _to_float(ultimo.get("custo_total_wei")),
        "custo_total_iota": _to_float(ultimo.get("custo_total_iota")),
    })
    return resumo


def _gravar_media_lote(confirmadas):
    media = _media_do_lote(confirmadas)
    lote = len(_lotes_salvos()) + 1
    linha = {
        "lote": lote,
        "quando": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
        "amostras": TAMANHO_LOTE,
        "tempo_medio_envio_ms": media["tempo_medio_envio_ms"],
        "tempo_medio_confirmacao_ms": media["tempo_medio_confirmacao_ms"],
        "custo_medio_iota": media["custo_medio_iota"],
        "custo_medio_wei": media["custo_medio_wei"],
        "custo_total_iota": media["custo_total_iota"],
        "custo_total_wei": media["custo_total_wei"],
    }
    with CSV_RESUMO.open("a", newline="", encoding="utf-8") as fh:
        csv.DictWriter(fh, fieldnames=CSV_RESUMO_CAMPOS).writerow(linha)
    print(
        f"[MEDIA LOTE {lote}] tempo_envio={media['tempo_medio_envio_ms']} ms | "
        f"confirmacao={media['tempo_medio_confirmacao_ms']} ms | "
        f"custo={media['custo_medio_iota']} IOTA",
        flush=True,
    )


@app.route("/")
def indice():
    return jsonify({
        "ok": True,
        "atestar": "http://127.0.0.1:5000/atestar",
        "metodo_hardware": "POST /atestar",
        "metodo_navegador": "GET /atestar",
        "eventos": len(historico),
        "csv": str(CSV_TX),
        "resumo": _calcular_resumo(),
        "media_total": _ler_media_total(),
        "hardware_pronto": _hardware_pronto,
        "csv_media_total": str(CSV_MEDIA_TOTAL),
    })


@app.route("/atestar", methods=["GET", "POST"])
def atestar():
    if request.method == "GET":
        return render_template_string(
            PAGINA_ATESTAR,
            eventos=list(historico),
            total=len(historico),
            lan_ip=_lan_ip(),
            resumo=_calcular_resumo(),
            csv_tx=str(CSV_TX),
            csv_resumo=str(CSV_RESUMO),
            csv_media_total=str(CSV_MEDIA_TOTAL),
            media_total=_ler_media_total(),
            hardware_pronto=_hardware_pronto,
        )

    dados = None
    try:
        dados = request.get_json(force=True, silent=True)
        if not dados:
            _registrar_evento(message="JSON invalido ou ausente")
            return jsonify({"status": "error", "message": "JSON invalido ou ausente"}), 400

        firmware_hash_hex = dados.get("firmware_hash")
        hw_status = dados.get("status", True)
        temperatura = dados.get("temperature", dados.get("temperatura"))
        umidade = dados.get("humidity", dados.get("umidade"))

        if not _leitura_hardware_valida(temperatura, umidade):
            print(f"[IGNORADO] sem leitura DHT valida: {dados}", flush=True)
            _registrar_evento(
                temperature=temperatura,
                humidity=umidade,
                hw_status=hw_status,
                firmware_hash=firmware_hash_hex,
                message="Aguardando DHT11 (temperatura/umidade ausentes ou invalidas)",
            )
            return jsonify({
                "status": "ignored",
                "message": "Contagem inicia so apos leitura real do DHT11 (temperature e humidity numericos).",
            }), 200

        _marcar_hardware_pronto()

        if not firmware_hash_hex:
            _registrar_evento(
                temperature=temperatura,
                humidity=umidade,
                hw_status=hw_status,
                message="Campo firmware_hash ausente",
            )
            return jsonify({"status": "error", "message": "Campo firmware_hash ausente"}), 400

        firmware_hash_bytes = _normalizar_hash(firmware_hash_hex)
        if firmware_hash_bytes is None or not hash_esta_enrolado(firmware_hash_bytes):
            print(
                f"[403] firmware_hash len={len(str(firmware_hash_hex))} valor={firmware_hash_hex!r}",
                flush=True,
            )
            _registrar_evento(
                temperature=temperatura,
                humidity=umidade,
                hw_status=hw_status,
                firmware_hash=firmware_hash_hex,
                message="Hash de firmware nao enrolado (codigo alterado)",
            )
            return jsonify({
                "status": "error",
                "message": "Hash de firmware nao enrolado. Codigo alterado nao e aceito.",
                "esperado": "0x" + FIRMWARE_HASH_ESPERADO.hex(),
            }), 403
        inicio = time.perf_counter()
        nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
        data = contract.encode_abi("registrar", args=[firmware_hash_bytes, hw_status])
        gas_price = w3.eth.gas_price

        # IOTA EVM rejeita EIP-1559. Alguns nos reportam 1076 e validam 1075 (ou o inverso).
        chain_ids = []
        for cid in (CHAIN_ID, 1075, 1076):
            if cid not in chain_ids:
                chain_ids.append(cid)

        last_error = None
        tx_hash_hex = None
        for cid in chain_ids:
            txn = {
                "nonce": nonce,
                "to": Web3.to_checksum_address(CONTRACT_ADDRESS),
                "value": 0,
                "gas": 150000,
                "gasPrice": gas_price,
                "chainId": int(cid),
                "data": data,
            }
            signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
            raw = signed_txn.raw_transaction
            print(
                f"[TX] chainId={cid} v={signed_txn.v} tipo={hex(raw[0])} gasPrice={gas_price}",
                flush=True,
            )
            try:
                tx_hash = w3.eth.send_raw_transaction(raw)
                tx_hash_hex = w3.to_hex(tx_hash)
                break
            except Exception as send_err:
                last_error = send_err
                if "chain ID mismatch" not in str(send_err):
                    raise

        if tx_hash_hex is None:
            raise last_error

        tempo_envio_ms = round((time.perf_counter() - inicio) * 1000, 2)
        recibo = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120, poll_latency=1)
        tempo_confirmacao_ms = round((time.perf_counter() - inicio) * 1000, 2)
        gas_usado = int(recibo.gasUsed)
        custo_wei = gas_usado * int(gas_price)
        custo_iota = float(w3.from_wei(custo_wei, "ether"))

        _append_csv({
            "quando": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success",
            "tx_hash": tx_hash_hex,
            "tempo_envio_ms": tempo_envio_ms,
            "tempo_confirmacao_ms": tempo_confirmacao_ms,
            "gas_price_wei": int(gas_price),
            "gas_usado": gas_usado,
            "custo_wei": custo_wei,
            "custo_iota": f"{custo_iota:.18f}".rstrip("0").rstrip("."),
            "temperature": temperatura,
            "humidity": umidade,
            "mensagem": "",
        })
        _registrar_evento(
            ok=True,
            status="success",
            temperature=temperatura,
            humidity=umidade,
            hw_status=hw_status,
            firmware_hash=firmware_hash_hex,
            tx_hash=tx_hash_hex,
            tempo_confirmacao_ms=tempo_confirmacao_ms,
            custo_iota=custo_iota,
        )
        print(
            f"[SUCESSO] TX {tx_hash_hex} | {tempo_confirmacao_ms} ms | {custo_iota} IOTA",
            flush=True,
        )
        return jsonify({
            "status": "success",
            "tx_hash": tx_hash_hex,
            "tempo_envio_ms": tempo_envio_ms,
            "tempo_confirmacao_ms": tempo_confirmacao_ms,
            "gas_usado": gas_usado,
            "custo_wei": custo_wei,
            "custo_iota": custo_iota,
        }), 200

    except Exception as e:
        tempo_erro_ms = None
        if "inicio" in locals():
            tempo_erro_ms = round((time.perf_counter() - inicio) * 1000, 2)
        _append_csv({
            "quando": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "error",
            "tx_hash": "",
            "tempo_envio_ms": tempo_erro_ms if tempo_erro_ms is not None else "",
            "tempo_confirmacao_ms": "",
            "gas_price_wei": "",
            "gas_usado": "",
            "custo_wei": "",
            "custo_iota": "",
            "temperature": dados.get("temperature") if isinstance(dados, dict) else "",
            "humidity": dados.get("humidity") if isinstance(dados, dict) else "",
            "mensagem": str(e),
        })
        _registrar_evento(
            temperature=dados.get("temperature") if isinstance(dados, dict) else None,
            humidity=dados.get("humidity") if isinstance(dados, dict) else None,
            hw_status=dados.get("status") if isinstance(dados, dict) else None,
            firmware_hash=dados.get("firmware_hash") if isinstance(dados, dict) else None,
            message=str(e),
        )
        print(f"[ERRO] Falha ao processar atestação: {str(e)}", flush=True)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    _garantir_csv()
    with CSV_RESUMO.open("w", newline="", encoding="utf-8") as fh:
        csv.DictWriter(fh, fieldnames=CSV_RESUMO_CAMPOS).writeheader()
    lan = _lan_ip()
    print(f"Relay contínuo em http://127.0.0.1:5000/atestar (chainId={CHAIN_ID})", flush=True)
    print(f"ESP32 na mesma Wi-Fi deve usar http://{lan}:5000/atestar", flush=True)
    print(f"CSV de desempenho: {CSV_TX}", flush=True)
    print(f"CSV media total: {CSV_MEDIA_TOTAL}", flush=True)
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)
