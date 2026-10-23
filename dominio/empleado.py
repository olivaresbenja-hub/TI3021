"""Empleado con gerente representado mediante un rol modificable."""
from datetime import date
from .persona import Persona
from .validaciones import fecha, positivo, identificador
from .excepciones import DatoInvalidoError


class Empleado(Persona):
    """Reutiliza Persona y añade condiciones laborales y asignaciones."""

    def __init__(self, nombre: str, direccion: str, telefono: str, email: str,
                 fecha_inicio: str, salario: float, departamento_id: int = None,
                 rol: str = 'empleado', id: int = None):
        """Valida también el salario inicial, no solo sus modificaciones."""
        super().__init__(nombre, direccion, telefono, email, id)
        self.fecha_inicio = fecha_inicio
        self.salario = salario
        self.departamento_id = identificador(departamento_id, opcional=True)
        self.rol = rol

    @property
    def fecha_inicio(self) -> date:
        """Lee la fecha del contrato."""
        return self._fecha_inicio

    @fecha_inicio.setter
    def fecha_inicio(self, valor: str):
        """Comprueba el día del calendario."""
        self._fecha_inicio = fecha(valor)

    @property
    def salario(self) -> float:
        """Lee el salario mediante el acceso público previsto."""
        return self._salario

    @salario.setter
    def salario(self, valor: float):
        """Impide salarios cero, negativos y no finitos."""
        self._salario = positivo(valor, 'Salario')

    @property
    def rol(self) -> str:
        """Lee el cargo actual sin cambiar la clase del empleado."""
        return self._rol

    @rol.setter
    def rol(self, valor: str):
        """Limita los roles a las opciones previstas."""
        if valor not in ('empleado', 'gerente'):
            raise DatoInvalidoError('El rol debe ser empleado o gerente.')
        self._rol = valor

    def subir_salario(self, aumento: float):
        """Aplica un aumento positivo y valida el resultado."""
        self.salario = self.salario + positivo(aumento, 'Aumento')

    def asignar_departamento(self, departamento):
        """Cambia la pertenencia; el repositorio guarda después el empleado."""
        self.departamento_id = identificador(departamento.id)

    def __str__(self) -> str:
        """Representa al empleado de manera legible en consola."""
        return (f'[{self.id}] {self.nombre} | {self.rol} | {self.email} '
                f'| salario {self.salario:.2f} | departamento {self.departamento_id}')
