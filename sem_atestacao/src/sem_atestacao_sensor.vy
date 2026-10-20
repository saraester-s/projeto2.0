#pragma version ^0.4.0

# Clone sem atestação: grava só a leitura do sensor (temp, umidade, status).

struct RegistroIoT:
    temperatura: uint256
    umidade: uint256
    hardwareValido: bool
    timestamp: uint256

historico: public(HashMap[address, HashMap[uint256, RegistroIoT]])
contagem_leituras: public(HashMap[address, uint256])

owner: public(address)
dispositivos_autorizados: public(HashMap[address, bool])

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

@external
def registrar_leitura(_temp: uint256, _umid: uint256, _status: bool):
    assert self.dispositivos_autorizados[msg.sender], "Dispositivo nao autorizado"
    assert _temp <= 100, "Temperatura fora da faixa plausivel"
    assert _umid <= 100, "Umidade fora da faixa plausivel"

    novo_registro: RegistroIoT = RegistroIoT(
        temperatura=_temp,
        umidade=_umid,
        hardwareValido=_status,
        timestamp=block.timestamp
    )

    indice_atual: uint256 = self.contagem_leituras[msg.sender]
    self.historico[msg.sender][indice_atual] = novo_registro
    self.contagem_leituras[msg.sender] += 1
    log LeituraRegistrada(msg.sender, _temp, _umid, _status, block.timestamp)
