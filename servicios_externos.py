"""Validación y transformación de los datos de Open-Meteo y Mi Indicador."""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import re

from api_cliente import ServicioError, obtener_json

GEOCODIFICACION = 'https://geocoding-api.open-meteo.com/v1/search'
PRONOSTICO = 'https://api.open-meteo.com/v1/forecast'
INDICADORES = 'https://mindicador.cl/api'
MONEDAS = {'USD': 'dolar', 'EUR': 'euro'}
ESTADOS = {
    0: 'Despejado', 1: 'Mayormente despejado', 2: 'Parcialmente nublado', 3: 'Cubierto',
    45: 'Niebla', 48: 'Niebla con escarcha', 51: 'Llovizna leve',
    53: 'Llovizna moderada', 55: 'Llovizna intensa', 56: 'Llovizna helada leve',
    57: 'Llovizna helada intensa', 61: 'Lluvia leve', 63: 'Lluvia moderada',
    65: 'Lluvia intensa', 66: 'Lluvia helada leve', 67: 'Lluvia helada intensa',
    71: 'Nieve leve', 73: 'Nieve moderada', 75: 'Nieve intensa', 77: 'Granos de nieve',
    80: 'Chubascos leves', 81: 'Chubascos moderados', 82: 'Chubascos intensos',
    85: 'Chubascos de nieve leves', 86: 'Chubascos de nieve intensos',
    95: 'Tormenta', 96: 'Tormenta con granizo leve', 99: 'Tormenta con granizo intenso',
}

def numero(valor, minimo, maximo):
    if type(valor) not in (float, int) or not minimo <= valor <= maximo:
        raise ValueError
    return valor


class Deserializador:
    """Convierte las respuestas JSON a datos validados que EcoTech puede usar."""

    @staticmethod
    def ubicaciones(datos, pais):
        lugares = []
        resultados = datos.get('results', [])
        if not isinstance(resultados, list):
            raise ServicioError('El proveedor devolvió una lista de ubicaciones inválida.')
        for fila in resultados:
            try:
                if fila['country_code'] != pais:
                    continue
                nombre = fila['name']
                region = fila.get('admin1', '')
                if not isinstance(nombre, str) or not nombre.isprintable() or not nombre.strip():
                    raise ValueError
                if not isinstance(region, str) or (region and not region.isprintable()):
                    raise ValueError
                etiqueta = ', '.join(item for item in (nombre, region, pais) if item)
                lugares.append((etiqueta, numero(fila['latitude'], -90, 90),
                                numero(fila['longitude'], -180, 180)))
            except (KeyError, ValueError, TypeError):
                continue
        if not lugares:
            raise ServicioError('No se encontraron ubicaciones válidas en el país indicado.')
        return lugares

    @staticmethod
    def clima(datos, etiqueta):
        try:
            actual = datos['current']
            instante = datetime.strptime(actual['time'], '%Y-%m-%dT%H:%M')
            temperatura = numero(actual['temperature_2m'], -100, 70)
            humedad = numero(actual['relative_humidity_2m'], 0, 100)
            codigo = actual['weather_code']
            if type(codigo) is not int:
                raise ValueError
            estado = ESTADOS[codigo]
        except (KeyError, ValueError, TypeError):
            raise ServicioError('El proveedor devolvió datos de clima inválidos.') from None
        return {'lugar': etiqueta, 'fecha': f'{instante:%Y-%m-%d %H:%M} UTC',
                'temperatura': temperatura, 'humedad': humedad, 'estado': estado,
                'fuente': 'Open-Meteo'}

    @staticmethod
    def cotizacion(datos, moneda):
        try:
            if datos['codigo'] != MONEDAS[moneda] or datos['unidad_medida'] != 'Pesos':
                raise ValueError
            ultima = max(datos['serie'], key=lambda fila: fecha_indicador(fila['fecha']))
            fecha = fecha_indicador(ultima['fecha'])
            tasa = str(Decimal(str(numero(ultima['valor'], 0.01, 1_000_000))))
        except (AttributeError, KeyError, ValueError, TypeError):
            raise ServicioError('El proveedor devolvió un tipo de cambio inválido.') from None
        return {'moneda': moneda, 'fecha': fecha.date().isoformat(),
                'tasa': tasa, 'fuente': 'Mi Indicador'}


def fecha_indicador(valor):
    fecha = datetime.fromisoformat(valor.replace('Z', '+00:00'))
    if fecha.tzinfo is None:
        raise ValueError
    return fecha


def validar_ubicacion(ciudad, pais):
    ciudad = ' '.join(ciudad.split())
    pais = pais.strip().upper()
    if not 2 <= len(ciudad) <= 70 or not any(c.isalpha() for c in ciudad):
        raise ServicioError('Escribe un nombre de ciudad de 2 a 70 caracteres.')
    if not all(c.isalnum() or c in " -.'’" for c in ciudad):
        raise ServicioError('La ciudad contiene caracteres inválidos.')
    if not re.fullmatch(r'[A-Z]{2}', pais):
        raise ServicioError('Usa un código de país de dos letras, por ejemplo CL o ES.')
    return ciudad, pais


def buscar_ciudades(ciudad, pais):
    datos = obtener_json(GEOCODIFICACION, {
        'name': ciudad, 'countryCode': pais, 'count': 5, 'language': 'es',
    })
    return Deserializador.ubicaciones(datos, pais)


def consultar_clima(lugar):
    etiqueta, latitud, longitud = lugar
    datos = obtener_json(PRONOSTICO, {
        'latitude': latitud, 'longitude': longitud, 'timezone': 'GMT',
        'current': 'temperature_2m,relative_humidity_2m,weather_code',
    })
    return Deserializador.clima(datos, etiqueta)


def validar_moneda(moneda):
    moneda = moneda.strip().upper()
    if moneda not in MONEDAS:
        raise ServicioError('Selecciona USD o EUR.')
    return moneda


def consultar_cotizacion(moneda):
    datos = obtener_json(f'{INDICADORES}/{MONEDAS[moneda]}')
    return Deserializador.cotizacion(datos, moneda)


def describir_clima(datos):
    return (f"{datos['lugar']} | {datos['fecha']} | {datos['temperatura']} °C | "
            f"{datos['estado']} | Humedad {datos['humedad']}% | {datos['fuente']}")


def describir_cotizacion(datos):
    return (f"1 {datos['moneda']} = {datos['tasa']} CLP | "
            f"Dato del {datos['fecha']} | {datos['fuente']}")


def convertir_salario(salario, datos):
    monto = Decimal(str(salario))
    if not monto.is_finite() or monto <= 0:
        raise ServicioError('El salario en CLP debe ser positivo y finito.')
    with localcontext() as contexto:
        contexto.prec = max(28, monto.adjusted() + 12)
        estimacion = (monto / Decimal(datos['tasa'])).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP)
    return (f"{monto:,.2f} CLP ≈ {estimacion:,.2f} {datos['moneda']} | "
            f"{describir_cotizacion(datos)}")
