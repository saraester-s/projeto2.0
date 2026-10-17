from flask import Flask, request, jsonify
from web3 import Web3

app = Flask(__name__)

# Configurações da Conexão com a IOTA EVM Testnet
RPC_URL = "https://json-rpc.evm.testnet.iotaledger.net"
CHAIN_ID = 1075

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Credenciais da carteira e dados do contrato ESDRA
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

@app.route('/atestar', methods=['POST'])
def atestar():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"status": "error", "message": "JSON invalido ou ausente"}), 400

        firmware_hash_hex = dados.get("firmware_hash")
        hw_status = dados.get("status", True)

        if not firmware_hash_hex:
            return jsonify({"status": "error", "message": "Campo firmware_hash ausente"}), 400

        firmware_hash_bytes = bytes.fromhex(firmware_hash_hex)
        nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
        
        # Constrói a transação aplicando explicitamente o gas, nonce e o Chain ID correto
        txn = contract.functions.registrar(firmware_hash_bytes, hw_status).build_transaction({
            'chainId': CHAIN_ID,
            'gas': 150000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': nonce,
        })

        signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_hash_hex = w3.to_hex(tx_hash)
        
        print(f"[SUCESSO] Atestação registrada! TX Hash: {tx_hash_hex}")
        return jsonify({"status": "success", "tx_hash": tx_hash_hex}), 200

    except Exception as e:
        print(f"[ERRO] Falha ao processar atestação: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)