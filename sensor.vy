# @version ^0.3.10

# 1. O molde dos dados do ESDRA
struct Atestacao:
    firmwareHash: bytes32
    timestamp: uint256
    isValid: bool

# 2. O armazenamento imutável
historico: public(HashMap[address, DynArray[Atestacao, 100]])

# 3. A função de registro chamada pelo dispositivo
@external
def registrar(_hash: bytes32, _status: bool):
    # Cria o pacote de dados usando a hora exata da rede
    nova_atestacao: Atestacao = Atestacao({
        firmwareHash: _hash,
        timestamp: block.timestamp,
        isValid: _status
    })
    
    # 4. SALVA o pacote no histórico do dispositivo (ESP32)
    self.historico[msg.sender].append(nova_atestacao)