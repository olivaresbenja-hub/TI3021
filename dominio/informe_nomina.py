"""Resumen de salarios, sin cálculo legal de remuneraciones."""
from .informe import Informe


class InformeNomina(Informe):
    """Suma los salarios actuales para demostrar un cálculo de negocio."""

    def __init__(self, empleados: list):
        """Recibe objetos del dominio, no una conexión SQL."""
        self.empleados = empleados

    def exportar(self) -> str:
        """Calcula el total de nómina y lo devuelve como texto."""
        total = 0
        for empleado in self.empleados:
            total = total + empleado.salario
        return f'Nómina: {len(self.empleados)} empleados; total salarios {total:.2f}'
