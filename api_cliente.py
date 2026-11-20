"""Cliente HTTP compartido por las dos APIs."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from time import sleep

import requests

from dominio.excepciones import EcoTechError

MAX_INTENTOS = 3
ESPERA_MAXIMA = 10


class ServicioError(EcoTechError):
    """Respuesta rechazada. Su mensaje se puede mostrar en el menú."""


class ServicioNoDisponible(ServicioError):
    """Fallo temporal del proveedor o de la red. Permite consultar la caché."""


def segundos_retry_after(valor):
    if not valor:
        return 0
    try:
        return max(0, int(valor))
    except ValueError:
        try:
            fecha = parsedate_to_datetime(valor)
            if fecha.tzinfo is None:
                return 0
            return max(0, (fecha - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            return 0


def obtener_json(url, parametros=None):
    """Devuelve un objeto JSON o traduce el fallo a un error del sistema."""
    for intento in range(MAX_INTENTOS):
        espera = 2 ** intento
        try:
            respuesta = requests.get(url, params=parametros, timeout=(4, 8), allow_redirects=False)
        except requests.exceptions.SSLError:
            raise ServicioError('Falló la verificación TLS del proveedor.') from None
        except (requests.Timeout, requests.ConnectionError):
            mensaje = 'No se pudo contactar al proveedor dentro del tiempo de espera.'
        except requests.RequestException:
            raise ServicioError('No se pudo completar la consulta externa.') from None
        else:
            estado = respuesta.status_code
            if estado == 200:
                try:
                    datos = respuesta.json()
                    if isinstance(datos, dict):
                        return datos
                except ValueError:
                    raise ServicioError('El proveedor devolvió un JSON inválido.') from None
                raise ServicioError('El proveedor devolvió un JSON con formato inesperado.')
            mensaje = f'El proveedor respondió con HTTP {estado}.'
            if estado == 429:
                espera = max(espera, segundos_retry_after(respuesta.headers.get('Retry-After')))
            elif not 500 <= estado <= 599:
                raise ServicioError(mensaje)

        if intento == MAX_INTENTOS - 1 or espera > ESPERA_MAXIMA:
            raise ServicioNoDisponible(mensaje)
        sleep(espera)
