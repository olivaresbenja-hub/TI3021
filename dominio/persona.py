"""Datos personales y su modificación controlada."""
from .validaciones import texto, correo, identificador


class Persona:
    """Centraliza los datos personales que reutiliza Empleado."""

    def __init__(self, nombre: str, direccion: str, telefono: str,
                 email: str, id: int = None):
        """Inicia los datos pasando por sus propiedades de validación."""
        self.id = identificador(id, opcional=True)
        self.nombre = nombre
        self.direccion = direccion
        self.telefono = telefono
        self.email = email

    @property
    def nombre(self) -> str:
        """Lee el nombre."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str):
        """Valida antes de cambiar el nombre."""
        self._nombre = texto(valor, 'Nombre')

    @property
    def direccion(self) -> str:
        """Lee la dirección."""
        return self._direccion

    @direccion.setter
    def direccion(self, valor: str):
        """Rechaza direcciones vacías."""
        self._direccion = texto(valor, 'Dirección')

    @property
    def telefono(self) -> str:
        """Lee el teléfono conservando prefijos y ceros."""
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str):
        """Valida que el teléfono no esté vacío."""
        self._telefono = texto(valor, 'Teléfono')

    @property
    def email(self) -> str:
        """Lee el correo."""
        return self._email

    @email.setter
    def email(self, valor: str):
        """Valida el formato antes de guardar el correo."""
        self._email = correo(valor)

    def actualizar_datos(self, nombre: str, email: str):
        """Valida ambos datos antes de modificar alguno."""
        nuevo_nombre = texto(nombre, 'Nombre')
        nuevo_email = correo(email)
        self.nombre = nuevo_nombre
        self.email = nuevo_email
