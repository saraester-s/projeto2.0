import os
import time
import random
import json
from web3 import Web3
from dotenv import load_dotenv

# 1. Carrega as variaveis secretas do arquivo .env
load_dotenv()

RPC_URL = os.getenv("RPC_URL")
CHAVE_PRIVADA = os.getenv("PRIVATE_KEY")
ENDERECO_CONTRATO = os.getenv("CONTRACT_ADDRESS")

# 2. Configura a conexao com a blockchain local (Ganache)
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    print("Erro: Nao foi possivel conectar a rede blockchain.")
    exit()

# Deriva o endereco publico a partir da chave privada
conta = w3.eth.account.from_key(CHAVE_PRIVADA)
endereco_carteira = conta.address

# 3. Carrega a ABI do Contrato e converte o Endereco para Checksum
with open('abi.json', 'r') as file:
    abi = json.load(file)

# A MÁGICA ACONTECE AQUI: O Python arruma as letras maiúsculas/minúsculas sozinho
endereco_formatado = Web3.to_checksum_address(ENDERECO_CONTRATO)
contrato = w3.eth.contract(address=endereco_formatado, abi=abi)

def simular_atestacao_esdra():
    print(f"Conectado com sucesso! Usando a carteira: {endereco_carteira}")
    print("Iniciando o simulador de atestacao de firmware (ESDRA)...")
    
    while True:
        # Simulando a verificacao de integridade do dispositivo
        versao_firmware = f"firmware_v1.0.{random.randint(0, 5)}"
        hash_firmware = Web3.keccak(text=versao_firmware)
        status_valido = random.choices([True, False], weights=[90, 10])[0]
        
        print(f"\nNovo pacote gerado:")
        print(f"   Versao Firmware base: {versao_firmware}")
        print(f"   Hash (bytes32): {hash_firmware.hex()}")
        print(f"   Estado valido: {status_valido}")
        
        try:
            # Montando a transacao chamando a funcao 'registrar' do contrato ESDRA
            tx = contrato.functions.registrar(hash_firmware, status_valido).build_transaction({
                'from': endereco_carteira,
                'nonce': w3.eth.get_transaction_count(endereco_carteira),
                'gas': 300000,
                'gasPrice': w3.eth.gas_price
            })
            
            # Assinando e transmitindo para o Ganache
            tx_assinada = w3.eth.account.sign_transaction(tx, private_key=CHAVE_PRIVADA)
            tx_hash = w3.eth.send_raw_transaction(tx_assinada.raw_transaction)
            
            print(f"Transacao de Atestacao enviada! Hash da Tx: {tx_hash.hex()}")
            
        except Exception as e:
            print(f"Falha no envio da atestacao: {e}")
            
        time.sleep(15)

if __name__ == "__main__":
    simular_atestacao_esdra()