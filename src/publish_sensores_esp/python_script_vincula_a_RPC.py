from web3 import Web3

# 1. Conexão RPC com a IOTA EVM Testnet
rpc_urls = [
    "https://json-rpc.evm.testnet.iotaledger.net",
    "https://json-rpc.evm.testnet.shimmer.network"
]

w3 = None
for url in rpc_urls:
    try:
        temp_w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 15}))
        if temp_w3.is_connected():
            w3 = temp_w3
            print(f"Conectado com sucesso ao nó RPC: {url}")
            break
    except Exception:
        continue

if not w3 or not w3.is_connected():
    raise ConnectionError("Não foi possível conectar a nenhum nó RPC da IOTA EVM Testnet.")

# 2. Configuração da Chave Privada e Conta
private_key = "0x547192f8e00d5f5e123539f1e8397cabb81dd7b1ff5b19b7e128187063423ba3"
account = w3.eth.account.from_key(private_key)

print(f"Endereço de envio: {account.address}")
print(f"Chain ID ativo: {w3.eth.chain_id}")

# 3. Bytecode do contrato ESDRA (^0.3.10)
bytecode = "6100fb61000f6000396100fb6000f35f3560e01c60026001821660011b6100f701601e395f51565b63a9ca9cd981186100ef576044361034176100f3576004358060a01c6100f3576040525f6040516020525f5260405f20600360243582548110156100f357026001820101905080546060526001810154608052600281015460a0525060606060f36100ef565b6305ef261c81186100ef576044361034176100f3576024358060011c6100f3576040526004356060524260805260405160a0525f336020525f5260405f208054606381116100f3576003810260018301016060518155608051600182015560a0516002820155506001810182555050005b5f5ffd5b5f80fd007e00188418fb810400a16576797065728300030a0013"

# 4. Construção da Transação de Deploy (Formato Legado seguro para EVM)
nonce = w3.eth.get_transaction_count(account.address)

tx = {
    'nonce': nonce,
    'gas': 3000000,
    'gasPrice': w3.eth.gas_price,
    'chainId': w3.eth.chain_id,
    'data': "0x" + bytecode
}

print("Assinando transação...")
signed_tx = w3.eth.account.sign_transaction(tx, private_key)

print("Enviando transação de deploy do contrato ESDRA para a IOTA EVM Testnet...")
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
print(f"Hash da Transação: {w3.to_hex(tx_hash)}")

print("Aguardando confirmação do bloco...")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print("\n" + "="*50)
print(" CONTRATO ESDRA PUBLICADO COM SUCESSO!")
print(f" Endereço do Contrato: {receipt.contractAddress}")
print("="*50)