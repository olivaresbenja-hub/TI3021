"""Contrato común de los informes por consola."""
from abc import ABC, abstractmethod


class Informe(ABC):
    """Exige a sus clases concretas un método exportar."""

    @abstractmethod
    def exportar(self) -> str:
        """Devuelve el contenido del informe como texto."""
