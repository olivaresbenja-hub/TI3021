"""Horas de trabajo asociadas a una asignación existente."""
from datetime import date
from .validaciones import fecha, positivo, texto, identificador


class RegistroTiempo:
    """Vincula un empleado, un proyecto y una jornada."""

    def __init__(self, empleado_id: int, proyecto_id: int, fecha: str,
                 horas: float, descripcion: str, id: int = None):
        """Inicia el registro con validaciones del dominio."""
        from .validaciones import fecha as convertir_fecha
        self.id = identificador(id, opcional=True)
        self.empleado_id = identificador(empleado_id)
        self.proyecto_id = identificador(proyecto_id)
        self.fecha = convertir_fecha(fecha)
        self.horas = horas
        self.descripcion = texto(descripcion, 'Descripción')

    @property
    def horas(self) -> float:
        """Lee las horas del registro."""
        return self._horas

    @horas.setter
    def horas(self, valor: float):
        """Limita cada registro a un máximo de 24 horas."""
        self._horas = positivo(valor, 'Horas', 24)

    def __str__(self) -> str:
        """Presenta el registro en consola."""
        return (f'[{self.id}] empleado {self.empleado_id} | proyecto {self.proyecto_id}'
                f' | {self.fecha} | {self.horas:g} h | {self.descripcion}')
