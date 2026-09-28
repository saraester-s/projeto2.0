#pragma version ^0.4.0

# 1. O molde dos dados do sensor
struct RegistroIoT:
    temperatura: uint256
    umidade: uint256
    hardwareValido: bool
    timestamp: uint256

# 2. O armazenamento infinito (Mapeia: Endereço da Placa -> Índice da Leitura -> Dados)
historico: public(HashMap[address, HashMap[uint256, RegistroIoT]])

# 3. Contador para saber quantas leituras cada placa já enviou
contagem_leituras: public(HashMap[address, uint256])

# 4. Controle de acesso: só dispositivos autorizados podem gravar dados
owner: public(address)
dispositivos_autorizados: public(HashMap[address, bool])

# 5. Evento emitido a cada registro válido, para auditoria/rastreabilidade externa
event LeituraRegistrada:
    dispositivo: indexed(address)
    temperatura: uint256
    umidade: uint256
    hardwareValido: bool
    timestamp: uint256

@deploy
def __init__():
    self.owner = msg.sender
    self.dispositivos_autorizados[msg.sender] = True

@external
def autorizar_dispositivo(_dispositivo: address):
    assert msg.sender == self.owner, "Somente o dono pode autorizar dispositivos"
    self.dispositivos_autorizados[_dispositivo] = True

@external
def revogar_dispositivo(_dispositivo: address):
    assert msg.sender == self.owner, "Somente o dono pode revogar dispositivos"
    self.dispositivos_autorizados[_dispositivo] = False

# 6. A função de registro otimizada
@external
def registrar_leitura(_temp: uint256, _umid: uint256, _status: bool):

    # Controle de acesso: só dispositivos autorizados podem gravar
    assert self.dispositivos_autorizados[msg.sender], "Dispositivo nao autorizado"

    # Validação de faixa: valores plausíveis de um DHT11 (0-100)
    assert _temp <= 100, "Temperatura fora da faixa plausivel"
    assert _umid <= 100, "Umidade fora da faixa plausivel"

    # Cria o pacote de dados do mundo real
    novo_registro: RegistroIoT = RegistroIoT(
        temperatura=_temp,
        umidade=_umid,
        hardwareValido=_status,
        timestamp=block.timestamp
    )

    # Pega o número da leitura atual da placa que chamou a função
    indice_atual: uint256 = self.contagem_leituras[msg.sender]

    # Guarda na gaveta exata daquela placa
    self.historico[msg.sender][indice_atual] = novo_registro

    # Prepara o contador para a próxima vez que o ESP32 enviar dados
    self.contagem_leituras[msg.sender] += 1

    # Emite o evento para auditoria/rastreabilidade externa
    log LeituraRegistrada(msg.sender, _temp, _umid, _status, block.timestamp)
