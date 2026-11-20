"""Cuenta local para la aplicación de consola."""
from getpass import getpass, GetPassWarning
from hashlib import pbkdf2_hmac
from hmac import compare_digest
import re
from warnings import catch_warnings, simplefilter

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from dominio.excepciones import EcoTechError

HASHER = PasswordHasher()


def leer_clave(mensaje):
    with catch_warnings():
        simplefilter('error', GetPassWarning)
        try:
            return getpass(mensaje)
        except GetPassWarning:
            raise EcoTechError('Abre el programa en una terminal interactiva.') from None


def guardar_usuario(base, usuario, clave):
    if not re.fullmatch(r'[a-z0-9_.-]{3,32}', usuario):
        raise EcoTechError('Usa de 3 a 32 letras sin tilde, números, puntos, guiones o _.')
    if not 12 <= len(clave) <= 128 or not clave.strip():
        raise EcoTechError('La contraseña debe tener de 12 a 128 caracteres.')
    hash_clave = HASHER.hash(clave)
    with base.conexion() as conn:
        conn.execute(
            'INSERT INTO usuario (id, nombre, hash_clave) VALUES (1, ?, ?)',
            (usuario, hash_clave),
        )


def iniciar_sesion(base):
    with base.conexion() as conn:
        cuenta = conn.execute(
            'SELECT nombre, hash_clave FROM usuario WHERE id = 1'
        ).fetchone()
        tabla_anterior = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'usuario_local'"
        ).fetchone()
        anterior = None
        if cuenta is None and tabla_anterior:
            anterior = conn.execute(
                'SELECT nombre, sal, derivado, iteraciones FROM usuario_local WHERE id = 1'
            ).fetchone()

    if cuenta is None and anterior is None:
        print('Primera ejecución. Crea tu cuenta local e ingresa con ella.')
        usuario = input('Nuevo usuario: ').strip().lower()
        clave = leer_clave('Nueva contraseña (mínimo 12 caracteres): ')
        if clave != leer_clave('Confirma la contraseña: '):
            raise EcoTechError('Las contraseñas ingresadas deben coincidir.')
        guardar_usuario(base, usuario, clave)
        return iniciar_sesion(base)

    for _ in range(3):
        usuario = input('Usuario: ').strip().lower()
        clave = leer_clave('Contraseña: ')
        if 12 <= len(clave) <= 128 and clave.strip():
            if cuenta is not None and verifica_clave(cuenta, usuario, clave):
                return True
            if anterior is not None and migrar_cuenta(base, anterior, usuario, clave):
                return True
        print('Credenciales inválidas.')
    print('Se agotaron los intentos de esta ejecución.')
    return False


def verifica_clave(cuenta, usuario, clave):
    nombre, hash_clave = cuenta
    try:
        return HASHER.verify(hash_clave, clave) and usuario == nombre
    except (VerificationError, InvalidHashError):
        return False


def migrar_cuenta(base, anterior, usuario, clave):
    """Actualiza el borrador local anterior solamente tras verificar su clave."""
    nombre, sal, derivado, iteraciones = anterior
    if not isinstance(iteraciones, int) or iteraciones != 600_000:
        return False
    calculado = pbkdf2_hmac('sha256', clave.encode('utf-8'), sal, iteraciones)
    if not compare_digest(calculado, derivado) or usuario != nombre:
        return False
    hash_clave = HASHER.hash(clave)
    with base.conexion() as conn:
        conn.execute('INSERT INTO usuario VALUES (1, ?, ?)', (usuario, hash_clave))
        conn.execute('DELETE FROM usuario_local WHERE id = 1')
    return True
