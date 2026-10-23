"""Errores que el menú puede explicar sin mostrar detalles de SQLite."""


class EcoTechError(Exception):
    """Error controlado del sistema."""


class DatoInvalidoError(EcoTechError, ValueError):
    """Un dato incumple una regla del dominio."""


class RegistroNoEncontradoError(EcoTechError):
    """No existe el registro solicitado."""


class DuplicadoError(EcoTechError):
    """El correo, nombre o asignación ya está registrado."""


class RelacionError(EcoTechError):
    """Una operación dejaría relaciones inconsistentes."""


class PersistenciaError(EcoTechError):
    """La base o su configuración no están disponibles."""
