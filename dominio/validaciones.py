"""Validaciones reutilizadas por los constructores y el menú."""
from datetime import date
from math import isfinite
from .excepciones import DatoInvalidoError

MAX_ID = 9223372036854775807


def texto(valor: str, campo: str) -> str:
    """Rechaza texto vacío y limita su extensión."""
    if not isinstance(valor, str) or not valor.strip() or len(valor.strip()) > 500:
        raise DatoInvalidoError(campo + ': escribe texto de 1 a 500 caracteres.')
    return valor.strip()


def correo(valor: str) -> str:
    """Comprueba un formato básico de correo, sin afirmar que la cuenta exista."""
    valor = texto(valor, 'Correo')
    if valor.count('@') != 1:
        raise DatoInvalidoError('El correo no tiene un formato válido.')
    for caracter in valor:
        if caracter.isspace():
            raise DatoInvalidoError('El correo no debe contener espacios.')
    usuario, dominio = valor.split('@')
    if not usuario or '.' not in dominio:
        raise DatoInvalidoError('El correo no tiene un formato válido.')
    for parte in dominio.split('.'):
        if not parte:
            raise DatoInvalidoError('El correo no tiene un formato válido.')
    return valor


def positivo(valor: float, campo: str, maximo: float = None) -> float:
    """Acepta números positivos y finitos, con un máximo opcional."""
    try:
        numero = float(valor)
    except (TypeError, ValueError, OverflowError) as error:
        raise DatoInvalidoError(campo + ': se requiere un número válido.') from error
    if isinstance(valor, bool) or not isfinite(numero) or numero <= 0:
        raise DatoInvalidoError(campo + ': debe ser mayor que cero y finito.')
    if maximo is not None and numero > maximo:
        raise DatoInvalidoError(campo + ': supera el máximo permitido.')
    return numero


def fecha(valor: str) -> date:
    """Convierte una fecha ISO y verifica que exista en el calendario."""
    if type(valor) is date:
        return valor
    try:
        if not isinstance(valor, str) or len(valor) != 10:
            raise ValueError('Formato')
        return date.fromisoformat(valor)
    except (TypeError, ValueError) as error:
        raise DatoInvalidoError('Fecha inválida. Usa AAAA-MM-DD.') from error


def identificador(valor: int, opcional: bool = False) -> int:
    """Impide IDs nulos obligatorios y enteros fuera del rango de SQLite."""
    if valor is None and opcional:
        return None
    if type(valor) is not int or not 1 <= valor <= MAX_ID:
        raise DatoInvalidoError('El ID debe estar entre 1 y 9223372036854775807.')
    return valor
