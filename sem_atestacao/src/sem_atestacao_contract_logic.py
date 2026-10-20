"""Espelho das regras de sem_atestacao_sensor.vy (sem hash de firmware)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegistroIoT:
    temperatura: int
    umidade: int
    hardwareValido: bool
    timestamp: int


class UnauthorizedDevice(Exception):
    pass


class OwnerOnly(Exception):
    pass


class OutOfRange(Exception):
    pass


class IoTContract:
    def __init__(self, owner: str, timestamp: int = 1_700_000_000):
        self.owner = owner
        self.dispositivos_autorizados: dict[str, bool] = {owner: True}
        self.historico: dict[str, dict[int, RegistroIoT]] = {}
        self.contagem_leituras: dict[str, int] = {}
        self.block_timestamp = timestamp
        self.eventos: list[tuple] = []

    def autorizar_dispositivo(self, sender: str, dispositivo: str) -> None:
        if sender != self.owner:
            raise OwnerOnly("Somente o dono pode autorizar dispositivos")
        self.dispositivos_autorizados[dispositivo] = True

    def revogar_dispositivo(self, sender: str, dispositivo: str) -> None:
        if sender != self.owner:
            raise OwnerOnly("Somente o dono pode revogar dispositivos")
        self.dispositivos_autorizados[dispositivo] = False

    def registrar_leitura(self, sender: str, temp: int, umid: int, status: bool) -> RegistroIoT:
        if not self.dispositivos_autorizados.get(sender, False):
            raise UnauthorizedDevice("Dispositivo nao autorizado")
        if temp > 100:
            raise OutOfRange("Temperatura fora da faixa plausivel")
        if umid > 100:
            raise OutOfRange("Umidade fora da faixa plausivel")

        registro = RegistroIoT(
            temperatura=temp,
            umidade=umid,
            hardwareValido=status,
            timestamp=self.block_timestamp,
        )
        indice = self.contagem_leituras.get(sender, 0)
        self.historico.setdefault(sender, {})[indice] = registro
        self.contagem_leituras[sender] = indice + 1
        self.eventos.append((sender, temp, umid, status, self.block_timestamp))
        return registro
