"""Configuración y transacciones con la biblioteca oficial sqlite3."""
from contextlib import contextmanager
from pathlib import Path
import os
import sqlite3
from dominio.excepciones import DuplicadoError, RelacionError, PersistenciaError

RAIZ = Path(__file__).resolve().parents[1]


def ruta_configurada() -> Path:
    """Lee una ruta local desde DB_NOMBRE; no ejecuta el contenido de .env."""
    ruta = os.environ.get('DB_NOMBRE')
    if not ruta:
        try:
            lineas = (RAIZ / '.env').read_text(encoding='utf-8-sig').splitlines()
        except (OSError, UnicodeError) as error:
            raise PersistenciaError('Copia .env.example a .env antes de iniciar.') from error
        for linea in lineas:
            clave, separador, valor = linea.partition('=')
            if separador and clave.strip() == 'DB_NOMBRE':
                ruta = valor.strip()
    if not ruta or '\x00' in ruta:
        raise PersistenciaError('Configura una ruta válida en DB_NOMBRE.')
    destino = Path(ruta).expanduser()
    if not destino.is_absolute():
        destino = RAIZ / destino
    return destino


class BaseDatos:
    """Centraliza la apertura, confirmación, reversión y cierre de SQLite."""

    def __init__(self, ruta: Path = None):
        """Permite una base temporal para pruebas sin tocar datos del usuario."""
        self.ruta = Path(ruta) if ruta is not None else ruta_configurada()

    @contextmanager
    def conexion(self):
        """Confirma al terminar; si falla, revierte y traduce el error."""
        conn = None
        try:
            conn = sqlite3.connect(str(self.ruta), timeout=5)
            conn.execute('PRAGMA foreign_keys = ON')
            conn.execute('BEGIN')
            yield conn
            conn.commit()
        except sqlite3.IntegrityError as error:
            if conn:
                conn.rollback()
            if 'UNIQUE' in str(error):
                raise DuplicadoError('Ese correo, nombre o asignación ya existe.') from error
            raise RelacionError(
                'Operación rechazada: revisa relaciones, responsable y total diario de horas.'
            ) from error
        except (sqlite3.Error, OSError) as error:
            if conn:
                conn.rollback()
            raise PersistenciaError(
                'No se pudo operar con la base. Revisa ruta y permisos.'
            ) from error
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def inicializar(self):
        """Crea las tablas de manera repetible usando un archivo SQL versionable."""
        try:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            esquema = (RAIZ / 'db' / '01_esquema.sql').read_text(encoding='utf-8')
        except (OSError, ValueError, UnicodeError) as error:
            raise PersistenciaError('No se pudo preparar la base o leer su esquema.') from error
        with self.conexion() as conn:
            conn.executescript(esquema)
