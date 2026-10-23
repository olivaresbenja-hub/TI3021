"""Resumen de horas de un proyecto."""
from .informe import Informe
from .proyecto import Proyecto


class InformeProyecto(Informe):
    """Aplica la misma interfaz exportar a un cálculo diferente."""

    def __init__(self, proyecto: Proyecto, registros: list):
        """Recibe el proyecto y los registros disponibles."""
        self.proyecto = proyecto
        self.registros = registros

    def exportar(self) -> str:
        """Suma solo las horas correspondientes al proyecto."""
        total = 0
        for registro in self.registros:
            if registro.proyecto_id == self.proyecto.id:
                total = total + registro.horas
        return f'Proyecto {self.proyecto.nombre}: {total:g} horas registradas'
