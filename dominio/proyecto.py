"""Datos del proyecto; las asignaciones se coordinan en el servicio."""
from datetime import date
from .validaciones import texto, fecha, identificador


class Proyecto:
    """Representa una iniciativa con empleados participantes."""

    def __init__(self, nombre: str, descripcion: str, fecha_inicio: str, id: int = None):
        """Valida todos los datos antes de utilizar el proyecto."""
        self.id = identificador(id, opcional=True)
        self.nombre = nombre
        self.descripcion = descripcion
        self.fecha_inicio = fecha_inicio

    @property
    def nombre(self) -> str:
        """Lee el nombre del proyecto."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str):
        """Comprueba que el nombre tenga contenido."""
        self._nombre = texto(valor, 'Proyecto')

    @property
    def descripcion(self) -> str:
        """Lee la descripción."""
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor: str):
        """Rechaza descripciones vacías."""
        self._descripcion = texto(valor, 'Descripción')

    @property
    def fecha_inicio(self) -> date:
        """Lee la fecha como date."""
        return self._fecha_inicio

    @fecha_inicio.setter
    def fecha_inicio(self, valor: str):
        """Verifica el formato y el día."""
        self._fecha_inicio = fecha(valor)

    def __str__(self) -> str:
        """Muestra los datos principales."""
        return f'[{self.id}] {self.nombre} | {self.fecha_inicio} | {self.descripcion}'
