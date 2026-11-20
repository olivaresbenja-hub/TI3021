"""Pruebas de autenticación, reintentos y respaldo local."""
from contextlib import redirect_stdout
from datetime import timedelta, datetime, timezone
from email.utils import format_datetime
from hashlib import pbkdf2_hmac
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

import requests
from argon2 import PasswordHasher, extract_parameters

from acceso import guardar_usuario
from api_cliente import ServicioError, ServicioNoDisponible, obtener_json, segundos_retry_after
from dominio.empleado import Empleado
from dominio.proyecto import Proyecto
from main import main
from repositorio.conexion import BaseDatos
from repositorio.sistema_repo import SistemaEcoTech
from servicios_externos import Deserializador

UBICACION = {'results': [
    {'country_code': 'CL', 'name': 'Santiago', 'latitude': -33.4, 'longitude': -70.7}
]}
CLIMA = {'current': {'time': '2026-11-19T12:00', 'temperature_2m': 18,
                     'relative_humidity_2m': 55, 'weather_code': 0}}
COTIZACION = {'codigo': 'dolar', 'unidad_medida': 'Pesos', 'serie': [
    {'fecha': '2026-11-18T00:00:00Z', 'valor': 900},
    {'fecha': '2026-11-19T00:00:00Z', 'valor': 1000},
]}


def respuesta(codigo=200, datos=None, headers=None):
    return Mock(status_code=codigo, json=Mock(return_value=datos), headers=headers or {})


class PruebasCliente(TestCase):
    def test_404_y_otros_4xx_sin_reintentos(self):
        for codigo in (400, 401, 403, 404):
            with self.subTest(codigo=codigo), patch('api_cliente.requests.get',
                                                    return_value=respuesta(codigo)) as get:
                with self.assertRaisesRegex(ServicioError, f'HTTP {codigo}'):
                    obtener_json('https://example.com')
                get.assert_called_once()

    def test_429_respeta_retry_after(self):
        respuestas = [respuesta(429, headers={'Retry-After': '5'}), respuesta(datos={'ok': True})]
        with patch('api_cliente.requests.get', side_effect=respuestas), patch('api_cliente.sleep') as espera:
            self.assertEqual(obtener_json('https://example.com'), {'ok': True})
            espera.assert_called_once_with(5)
        despues = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=30), usegmt=True)
        self.assertGreater(segundos_retry_after(despues), 28)
        with (
            patch('api_cliente.requests.get', return_value=respuesta(429, headers={'Retry-After': '90'})) as get,
            patch('api_cliente.sleep') as espera,
        ):
            with self.assertRaisesRegex(ServicioNoDisponible, 'HTTP 429'):
                obtener_json('https://example.com')
            get.assert_called_once()
            espera.assert_not_called()

    def test_red_y_5xx_reintentan_con_espera_creciente(self):
        respuestas = [requests.ConnectionError('detalle interno'), respuesta(502), respuesta(datos={'ok': True})]
        with patch('api_cliente.requests.get', side_effect=respuestas) as get, patch('api_cliente.sleep') as espera:
            self.assertEqual(obtener_json('https://example.com'), {'ok': True})
            self.assertEqual([llamada.args[0] for llamada in espera.call_args_list], [1, 2])
            self.assertTrue(all(llamada.kwargs['timeout'] == (4, 8) for llamada in get.call_args_list))

    def test_json_invalido_sin_detalles_ni_reintento(self):
        invalida = respuesta()
        invalida.json.side_effect = ValueError('detalle interno')
        with patch('api_cliente.requests.get', return_value=invalida) as get:
            with self.assertRaisesRegex(ServicioError, 'JSON inválido') as fallo:
                obtener_json('https://example.com')
            self.assertNotIn('detalle interno', str(fallo.exception))
            get.assert_called_once()

    def test_error_tls_se_informa_sin_reintento(self):
        with patch('api_cliente.requests.get', side_effect=requests.exceptions.SSLError) as get:
            with self.assertRaisesRegex(ServicioError, 'verificación TLS') as fallo:
                obtener_json('https://example.com')
            self.assertNotIsInstance(fallo.exception, ServicioNoDisponible)
            get.assert_called_once()

    def test_deserializador_filtra_filas_malas_y_rechaza_clima_incompleto(self):
        lugares = Deserializador.ubicaciones({'results': [{'country_code': 'CL'}, *UBICACION['results']]}, 'CL')
        self.assertEqual(lugares, [('Santiago, CL', -33.4, -70.7)])
        with self.assertRaisesRegex(ServicioError, 'clima inválidos'):
            Deserializador.clima({'current': {}}, 'Santiago')


class PruebasES3(TestCase):
    def setUp(self):
        temporal = TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.base = BaseDatos(Path(temporal.name) / 'prueba.db')
        self.base.inicializar()
        self.clave = 'Frase de contraseña ficticia'
        self.sistema = SistemaEcoTech(self.base)
        proyecto = self.sistema.proyectos.guardar(Proyecto('Proyecto Solar', 'Prueba', '2026-10-01'))
        empleado = self.sistema.contratar_en_proyecto(
            Empleado('Ana', 'Calle ficticia', '912345678', 'ana@example.com', '2026-10-01', 800000),
            proyecto.id,
        )
        self.proyecto = str(proyecto.id)
        self.empleado = str(empleado.id)
        self.clima = ['1', self.proyecto, 'Santiago', 'CL']
        self.conversion = ['2', self.proyecto, self.empleado, 'USD']

    def ejecutar(self, entradas, claves=None, codigo=0):
        salida = StringIO()
        with (
            patch('main.BaseDatos', return_value=BaseDatos(self.base.ruta)),
            patch('builtins.input', side_effect=entradas),
            patch('acceso.leer_clave', side_effect=claves or [self.clave]),
            redirect_stdout(salida),
        ):
            self.assertEqual(main(), codigo)
        return salida.getvalue()

    def datos_guardados(self):
        with self.base.conexion() as conn:
            return conn.execute('SELECT tipo, clave, obtenido_en, datos FROM dato_externo ORDER BY tipo').fetchall()

    def cargar_en_linea(self):
        with patch('api_cliente.requests.get', side_effect=[
            respuesta(datos=UBICACION), respuesta(datos=CLIMA), respuesta(datos=COTIZACION),
        ]) as get:
            salida = self.ejecutar(['alumno', '8', *self.clima, '1', *self.conversion, '0', '0'])
        self.assertIn('18 °C', salida)
        self.assertIn('800.00 USD', salida)
        # Al proveedor se le pide el indicador. La conversión se hace localmente.
        self.assertTrue(get.call_args.args[0].endswith('/dolar'))
        self.assertIsNone(get.call_args.kwargs['params'])

    def test_inspeccion_sqlite_y_acceso_rechazado(self):
        salida = self.ejecutar(['alumno', 'alumno', '0'], claves=[self.clave] * 3)
        self.assertIn('Servicios externos', salida)
        with self.base.conexion() as conn:
            hash_clave, = conn.execute('SELECT hash_clave FROM usuario').fetchone()
        self.assertNotIn(self.clave, hash_clave)
        self.assertTrue(hash_clave.startswith('$argon2id$'))
        self.assertEqual(extract_parameters(hash_clave).salt_len, 16)
        self.assertTrue(PasswordHasher().verify(hash_clave, self.clave))
        with patch('api_cliente.requests.get') as get:
            salida = self.ejecutar(['alumno'] * 3, claves=[''] * 3, codigo=1)
            self.assertNotIn('Servicios externos', salida)
            get.assert_not_called()

    def test_migra_cuenta_local_del_borrador_al_ingresar(self):
        sal = bytes(16)
        derivado = pbkdf2_hmac('sha256', self.clave.encode('utf-8'), sal, 600_000)
        with self.base.conexion() as conn:
            conn.execute(
                'CREATE TABLE usuario_local (id INTEGER, nombre TEXT, sal BLOB, '
                'derivado BLOB, iteraciones INTEGER)'
            )
            conn.execute('INSERT INTO usuario_local VALUES (1, ?, ?, ?, ?)',
                         ('alumno', sal, derivado, 600_000))
        self.assertIn('Servicios externos', self.ejecutar(['alumno', '0']))
        with self.base.conexion() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM usuario_local').fetchone(), (0,))
            hash_clave, = conn.execute('SELECT hash_clave FROM usuario').fetchone()
        self.assertTrue(PasswordHasher().verify(hash_clave, self.clave))

    def test_ejecucion_consecutiva_sin_duplicados(self):
        guardar_usuario(self.base, 'alumno', self.clave)
        self.cargar_en_linea()
        self.cargar_en_linea()
        filas = self.datos_guardados()
        self.assertEqual([(tipo, clave) for tipo, clave, _, _ in filas],
                         [('clima', 'CL:santiago'), ('cotización', 'USD')])
        self.assertNotIn('800000', filas[1][3])

    def test_corte_de_red_usa_datos_guardados_sin_reescribirlos(self):
        guardar_usuario(self.base, 'alumno', self.clave)
        self.cargar_en_linea()
        iniciales = self.datos_guardados()
        with (
            patch('api_cliente.requests.get', side_effect=requests.ConnectionError) as get,
            patch('api_cliente.sleep'),
        ):
            salida = self.ejecutar(['alumno', '8', *self.clima, *self.conversion, '0', '0'])
        self.assertEqual(get.call_count, 6)
        self.assertEqual(salida.count('Plan B: dato guardado hace'), 2)
        for fecha in (fila[2] for fila in iniciales):
            self.assertIn(f'obtenido_en: {fecha}', salida)
        self.assertEqual(self.datos_guardados(), iniciales)

    def test_404_y_sin_respaldo_vuelven_al_menu(self):
        guardar_usuario(self.base, 'alumno', self.clave)
        respuestas = [respuesta(404), *[requests.Timeout] * 3]
        with patch('api_cliente.requests.get', side_effect=respuestas) as get, patch('api_cliente.sleep'):
            salida = self.ejecutar(['alumno', '8', *self.clima, *self.clima, '0', '0'])
        self.assertEqual(get.call_count, 4)
        self.assertIn('HTTP 404', salida)
        self.assertIn('Todavía no hay datos guardados', salida)
        self.assertIn('Hasta luego', salida)
        self.assertEqual(self.datos_guardados(), [])
