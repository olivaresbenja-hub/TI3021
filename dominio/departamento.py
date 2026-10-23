"""Área organizacional con un responsable opcional."""
from .validaciones import texto, identificador


class Departamento:
    """Representa el departamento; la responsabilidad no crea otro tipo de persona."""

    def __init__(self, nombre: str, gerente_id: int = None, id: int = None):
        """Valida el nombre y los identificadores recibidos."""
        self.id = identificador(id, opcional=True)
        self.nombre = nombre
        self.gerente_id = identificador(gerente_id, opcional=True)

    @property
    def nombre(self) -> str:
        """Lee el nombre del área."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str):
        """Impide nombres vacíos."""
        self._nombre = texto(valor, 'Departamento')

    def asignar_empleado(self, empleado):
        """Asigna el departamento en el objeto empleado."""
        empleado.asignar_departamento(self)

    def __str__(self) -> str:
        """Muestra identificación y responsable."""
        return f'[{self.id}] {self.nombre} | responsable {self.gerente_id}'
