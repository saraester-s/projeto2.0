from pathlib import Path
from web3 import Web3

# Clone sem atestação: implanta sem_atestacao_sensor.vy (registrar_leitura), não o ESDRA.

rpc_urls = [
    "https://json-rpc.evm.testnet.iotaledger.net",
    "https://json-rpc.evm.testnet.shimmer.network",
    "https://json-rpc.evm.testnet.iota.cafe",
]

w3 = None
for url in rpc_urls:
    try:
        temp_w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 15}))
        if temp_w3.is_connected():
            w3 = temp_w3
            print(f"Conectado com sucesso ao nó RPC: {url}")
            break
    except Exception:
        continue

if not w3 or not w3.is_connected():
    raise ConnectionError("Não foi possível conectar a nenhum nó RPC da IOTA EVM Testnet.")

private_key = "0x547192f8e00d5f5e123539f1e8397cabb81dd7b1ff5b19b7e128187063423ba3"
account = w3.eth.account.from_key(private_key)

print(f"Endereço de envio: {account.address}")
print(f"Chain ID ativo: {w3.eth.chain_id}")

contrato_vy = Path(__file__).resolve().parents[1] / "sem_atestacao_sensor.vy"
try:
    import vyper
except ImportError as exc:
    raise SystemExit(
        "Instale vyper para compilar sem_atestacao_sensor.vy, depois rode de novo.\n"
        f"Arquivo: {contrato_vy}"
    ) from exc

print(f"Compilando {contrato_vy}...")
compiled = vyper.compile_codes(
    {str(contrato_vy): contrato_vy.read_text(encoding="utf-8")},
    output_formats=["bytecode"],
)
bytecode = compiled[str(contrato_vy)]["bytecode"]
if not str(bytecode).startswith("0x"):
    bytecode = "0x" + str(bytecode)

nonce = w3.eth.get_transaction_count(account.address)

tx = {
    "nonce": nonce,
    "gas": 3000000,
    "gasPrice": w3.eth.gas_price,
    "chainId": w3.eth.chain_id,
    "data": bytecode,
}

print("Assinando transação...")
signed_tx = w3.eth.account.sign_transaction(tx, private_key)

print("Enviando deploy de sem_atestacao_sensor.vy (somente registrar_leitura)...")
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
print(f"Hash da Transação: {w3.to_hex(tx_hash)}")

print("Aguardando confirmação do bloco...")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print("\n" + "=" * 50)
print(" CONTRATO SEM ATESTAÇÃO PUBLICADO")
print(f" Endereço do Contrato: {receipt.contractAddress}")
print(" Cole este endereço em CONTRACT_ADDRESS do relay.")
print("=" * 50)
