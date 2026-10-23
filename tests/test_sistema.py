"""Regresiones de la auditoría y pruebas de negocio con datos ficticios."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import ast
import unittest

from dominio.empleado import Empleado
from dominio.departamento import Departamento
from dominio.proyecto import Proyecto
from dominio.registro_tiempo import RegistroTiempo
from dominio.informe import Informe
from dominio.informe_nomina import InformeNomina
from dominio.informe_proyecto import InformeProyecto
from dominio.excepciones import (
    DatoInvalidoError, DuplicadoError, RelacionError,
    PersistenciaError, RegistroNoEncontradoError,
)
from dominio.validaciones import MAX_ID
from repositorio.conexion import BaseDatos, ruta_configurada
from repositorio.sistema_repo import SistemaEcoTech
from main import main, formulario_empleado, formulario_proyecto, formulario_registro
from dominio.validaciones import correo


class PruebasEcoTech(unittest.TestCase):
    """Cada prueba trabaja sobre su propia base, nunca sobre datos del menú."""

    def setUp(self):
        """Prepara una base descartable dentro del directorio de pruebas."""
        self.temporal = TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temporal.cleanup)
        self.base = BaseDatos(Path(self.temporal.name) / 'prueba.db')
        self.base.inicializar()
        self.sistema = SistemaEcoTech(self.base)

    def nuevo_empleado(self, nombre='Ana', email='ana@ecotech.cl', rol='empleado'):
        """Construye un empleado sin guardarlo."""
        return Empleado(nombre, 'Calle 123', '912345678', email,
                        '2026-10-01', 800000, rol=rol)

    def nuevo_proyecto(self, nombre='Solar'):
        """Guarda un proyecto y devuelve el ID asignado."""
        return self.sistema.proyectos.guardar(Proyecto(nombre, 'Pruebas', '2026-10-01'))

    def nueva_asignacion(self):
        """Prepara empleado y proyecto relacionados."""
        empleado = self.sistema.empleados.guardar(self.nuevo_empleado())
        proyecto = self.nuevo_proyecto()
        self.sistema.vincular(empleado.id, proyecto.id)
        return empleado, proyecto

    def test_crud_empleado_persistencia(self):
        """Comprueba el ciclo completo y una conexión independiente."""
        repo = self.sistema.empleados
        empleado = repo.guardar(self.nuevo_empleado())
        otro = SistemaEcoTech(BaseDatos(self.base.ruta))
        self.assertEqual(otro.empleados.obtener(empleado.id).nombre, 'Ana')
        empleado.subir_salario(20000)
        repo.actualizar(empleado)
        self.assertEqual(otro.empleados.obtener(empleado.id).salario, 820000)
        repo.eliminar(empleado.id)
        self.assertIsNone(repo.obtener(empleado.id))

    def test_crud_departamento(self):
        """Comprueba cambios y borrado del departamento."""
        repo = self.sistema.departamentos
        dep = repo.guardar(Departamento('Ventas'))
        dep.nombre = 'Operaciones'
        repo.actualizar(dep)
        self.assertEqual(repo.obtener(dep.id).nombre, 'Operaciones')
        repo.eliminar(dep.id)
        self.assertEqual(repo.listar(), [])

    def test_crud_proyecto(self):
        """Comprueba cambios y borrado del proyecto."""
        repo = self.sistema.proyectos
        proyecto = self.nuevo_proyecto()
        proyecto.descripcion = 'Descripción actualizada'
        repo.actualizar(proyecto)
        self.assertEqual(repo.obtener(proyecto.id).descripcion, 'Descripción actualizada')
        repo.eliminar(proyecto.id)
        self.assertEqual(repo.listar(), [])

    def test_crud_registro(self):
        """Comprueba las cuatro operaciones de horas."""
        empleado, proyecto = self.nueva_asignacion()
        repo = self.sistema.registros
        registro = repo.guardar(RegistroTiempo(
            empleado.id, proyecto.id, '2026-10-22', 4, 'Pruebas'))
        registro.horas = 6
        repo.actualizar(registro)
        self.assertEqual(repo.obtener(registro.id).horas, 6)
        repo.eliminar(registro.id)
        self.assertEqual(repo.listar(), [])

    def test_ids_fuera_de_rango_rechazados(self):
        """Regresión del OverflowError encontrado en la versión anterior."""
        for valor in (0, -1, True, '1', MAX_ID + 1, 10 ** 100):
            with self.subTest(valor=valor):
                with self.assertRaises(DatoInvalidoError):
                    self.sistema.empleados.obtener(valor)
        self.assertIsNone(self.sistema.empleados.obtener(MAX_ID))

    def test_menu_no_se_cierra_por_id_enorme(self):
        """El menú explica la entrada inválida y admite salir normalmente."""
        salida = StringIO()
        entradas = ['1', '3', str(10 ** 30), '0', '0']
        with patch('main.BaseDatos', return_value=self.base):
            with patch('builtins.input', side_effect=entradas), redirect_stdout(salida):
                self.assertEqual(main(), 0)
        self.assertIn('No se completó', salida.getvalue())
        self.assertIn('Hasta luego', salida.getvalue())

    def test_salario_y_aumento_no_alteran_estado_invalido(self):
        """La propiedad conserva el valor anterior al rechazar una entrada."""
        empleado = self.nuevo_empleado()
        for valor in (-1, 0, float('nan'), float('inf'), 'texto', True):
            with self.assertRaises(DatoInvalidoError):
                empleado.salario = valor
            with self.assertRaises(DatoInvalidoError):
                empleado.subir_salario(valor)
            self.assertEqual(empleado.salario, 800000)

    def test_actualizar_datos_no_deja_cambio_parcial(self):
        """Valida los dos datos antes de cambiarlos."""
        empleado = self.nuevo_empleado()
        with self.assertRaises(DatoInvalidoError):
            empleado.actualizar_datos('Otra', 'correo_invalido')
        self.assertEqual(empleado.nombre, 'Ana')

    def test_fechas_y_campos_vacios(self):
        """Impide fechas inexistentes y texto vacío al crear y modificar."""
        with self.assertRaises(DatoInvalidoError):
            Proyecto('X', 'Descripción', '2026-02-30')
        with self.assertRaises(DatoInvalidoError):
            Departamento('   ')
        empleado = self.nuevo_empleado()
        with self.assertRaises(DatoInvalidoError):
            empleado.direccion = ''

    def test_gerente_es_rol_modificable(self):
        """Cambiar de rol conserva la misma clase y el mismo ID."""
        empleado = self.sistema.empleados.guardar(self.nuevo_empleado())
        id_original = empleado.id
        empleado.rol = 'gerente'
        self.sistema.empleados.actualizar(empleado)
        recuperado = self.sistema.empleados.obtener(id_original)
        self.assertIs(type(recuperado), Empleado)
        self.assertEqual(recuperado.rol, 'gerente')

    def test_rol_invalido(self):
        """Limita el rol a las opciones del modelo."""
        with self.assertRaises(DatoInvalidoError):
            self.nuevo_empleado(rol='administrador_inventado')

    def test_correo_duplicado_error_negocio(self):
        """Traduce el error UNIQUE y conserva el registro original."""
        self.sistema.empleados.guardar(self.nuevo_empleado())
        with self.assertRaises(DuplicadoError):
            self.sistema.empleados.guardar(self.nuevo_empleado('Otra', 'ANA@ECOTECH.CL'))
        self.assertEqual(len(self.sistema.empleados.listar()), 1)

    def test_busqueda_payload_y_comillas_literal(self):
        """Aísla entradas de usuario de la sintaxis SQL."""
        self.sistema.empleados.guardar(self.nuevo_empleado())
        self.assertEqual(self.sistema.empleados.buscar("' OR '1'='1"), [])
        texto = "X'); DROP TABLE empleado; --"
        empleado = self.sistema.empleados.guardar(self.nuevo_empleado(texto, 'x@ecotech.cl'))
        self.assertEqual(self.sistema.empleados.obtener(empleado.id).nombre, texto)
        self.assertEqual(len(self.sistema.empleados.buscar(texto)), 1)
        self.assertEqual(len(self.sistema.empleados.listar()), 2)

    def test_sql_no_se_construye_en_tiempo_de_ejecucion(self):
        """Impide reintroducir f-strings, suma de cadenas o format en execute."""
        raiz = Path(__file__).resolve().parents[1]
        for carpeta in ('repositorio',):
            for archivo in (raiz / carpeta).glob('*.py'):
                arbol = ast.parse(archivo.read_text(encoding='utf-8'))
                for nodo in ast.walk(arbol):
                    if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
                        if nodo.func.attr in ('execute', 'executemany'):
                            self.assertIsInstance(nodo.args[0], (ast.Constant, ast.Attribute))
        arbol = ast.parse((raiz / 'repositorio/sistema_repo.py').read_text(encoding='utf-8'))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
                if nodo.func.attr == 'execute':
                    self.assertIsInstance(nodo.args[0], ast.Constant)

    def test_asignar_y_retirar_se_guardan(self):
        """Regresión de las asignaciones que antes quedaban solo en memoria."""
        empleado, proyecto = self.nueva_asignacion()
        otro = SistemaEcoTech(BaseDatos(self.base.ruta))
        self.assertEqual(len(otro.relaciones()), 1)
        self.sistema.desvincular(empleado.id, proyecto.id)
        self.assertEqual(otro.relaciones(), [])

    def test_asignacion_duplicada(self):
        """Rechaza una segunda relación idéntica."""
        empleado, proyecto = self.nueva_asignacion()
        with self.assertRaises(DuplicadoError):
            self.sistema.vincular(empleado.id, proyecto.id)

    def test_horas_exigen_asignacion(self):
        """La clave compuesta evita registrar horas sin participación."""
        empleado = self.sistema.empleados.guardar(self.nuevo_empleado())
        proyecto = self.nuevo_proyecto()
        with self.assertRaises(RelacionError):
            self.sistema.registros.guardar(RegistroTiempo(
                empleado.id, proyecto.id, '2026-10-22', 4, 'Sin asignación'))

    def test_horas_diarias_limite_y_actualizacion(self):
        """No permite sumar más de 24 horas, ni al insertar ni al editar."""
        empleado, proyecto = self.nueva_asignacion()
        primero = self.sistema.registros.guardar(RegistroTiempo(
            empleado.id, proyecto.id, '2026-10-22', 20, 'Primero'))
        segundo = self.sistema.registros.guardar(RegistroTiempo(
            empleado.id, proyecto.id, '2026-10-22', 4, 'Segundo'))
        with self.assertRaises(RelacionError):
            self.sistema.registros.guardar(RegistroTiempo(
                empleado.id, proyecto.id, '2026-10-22', 1, 'Exceso'))
        segundo.horas = 5
        with self.assertRaises(RelacionError):
            self.sistema.registros.actualizar(segundo)
        self.assertEqual(self.sistema.registros.obtener(segundo.id).horas, 4)
        primero.horas = 19
        self.sistema.registros.actualizar(primero)

    def test_horas_individuales_invalidas(self):
        """Rechaza cantidades inválidas antes de llegar a SQLite."""
        for horas in (-1, 0, 25, float('nan')):
            with self.assertRaises(DatoInvalidoError):
                RegistroTiempo(1, 1, '2026-10-22', horas, 'Pruebas')

    def test_borrados_no_pierden_historial(self):
        """Un empleado con horas no puede desaparecer ni desvincularse."""
        empleado, proyecto = self.nueva_asignacion()
        self.sistema.registros.guardar(RegistroTiempo(
            empleado.id, proyecto.id, '2026-10-22', 4, 'Trabajo'))
        with self.assertRaises(RelacionError):
            self.sistema.empleados.eliminar(empleado.id)
        with self.assertRaises(RelacionError):
            self.sistema.proyectos.eliminar(proyecto.id)
        with self.assertRaises(RelacionError):
            self.sistema.desvincular(empleado.id, proyecto.id)

    def test_responsable_debe_tener_rol_gerente(self):
        """Valida el rol antes de modificar responsabilidades."""
        empleado = self.sistema.empleados.guardar(self.nuevo_empleado())
        dep = self.sistema.departamentos.guardar(Departamento('Ventas'))
        with self.assertRaises(RelacionError):
            self.sistema.asignar_gerente(empleado.id, dep.id)
        empleado.rol = 'gerente'
        self.sistema.empleados.actualizar(empleado)
        self.sistema.asignar_gerente(empleado.id, dep.id)
        self.assertEqual(self.sistema.departamentos.obtener(dep.id).gerente_id, empleado.id)

    def test_responsable_no_puede_perder_rol_sin_retirarlo(self):
        """El repositorio conserva coherentes responsabilidad y rol."""
        empleado = self.sistema.empleados.guardar(self.nuevo_empleado(rol='gerente'))
        dep = self.sistema.departamentos.guardar(Departamento('Ventas'))
        self.sistema.asignar_gerente(empleado.id, dep.id)
        empleado.rol = 'empleado'
        with self.assertRaises(RelacionError):
            self.sistema.empleados.actualizar(empleado)
        self.sistema.quitar_gerente(dep.id)
        self.sistema.empleados.actualizar(empleado)

    def test_contratacion_atomica_exitosa(self):
        """Confirma conjuntamente el empleado y su relación."""
        proyecto = self.nuevo_proyecto()
        empleado = self.nuevo_empleado()
        self.sistema.contratar_en_proyecto(empleado, proyecto.id)
        self.assertIsNotNone(empleado.id)
        self.assertEqual(len(self.sistema.relaciones()), 1)

    def test_contratacion_revierte_primera_escritura(self):
        """La segunda escritura falla por FK y revierte la primera."""
        empleado = self.nuevo_empleado()
        with self.assertRaises(RelacionError):
            self.sistema.contratar_en_proyecto(empleado, 999)
        self.assertIsNone(empleado.id)
        self.assertEqual(self.sistema.empleados.listar(), [])
        self.assertEqual(self.sistema.relaciones(), [])

    def test_informes_polimorficos(self):
        """Dos clases concretas responden exportar con cálculos distintos."""
        empleado, proyecto = self.nueva_asignacion()
        registro = RegistroTiempo(empleado.id, proyecto.id, '2026-10-22', 4, 'Trabajo')
        informes = [InformeNomina([empleado]), InformeProyecto(proyecto, [registro])]
        salidas = [informe.exportar() for informe in informes]
        self.assertIn('800000.00', salidas[0])
        self.assertIn('4 horas', salidas[1])
        with self.assertRaises(TypeError):
            Informe()

    def test_no_encontrado_y_claves_foraneas(self):
        """Traduce fallos de registro y relaciones a errores del negocio."""
        with self.assertRaises(RegistroNoEncontradoError):
            self.sistema.empleados.eliminar(999)
        empleado = self.nuevo_empleado()
        empleado.departamento_id = 999
        with self.assertRaises(RelacionError):
            self.sistema.empleados.guardar(empleado)

    def test_esquema_repetible_y_conexion_fallida(self):
        """Inicializar dos veces conserva la estructura; una ruta mala se informa."""
        self.base.inicializar()
        with self.assertRaises(PersistenciaError):
            with BaseDatos(Path(self.temporal.name) / 'sin_carpeta' / 'x.db').conexion():
                pass

    def test_configuracion_ausente(self):
        """La falta de .env produce un error de configuración comprensible."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('repositorio.conexion.RAIZ', Path(self.temporal.name)):
                with self.assertRaises(PersistenciaError):
                    ruta_configurada()

    def test_menu_crud_completo(self):
        """Recorre creación, consulta, edición y eliminación con entradas reales."""
        entradas = ['1', '1', 'Ana', 'Calle 123', '123', 'ana@ecotech.cl',
                    '2026-10-01', '800000', 'empleado', '', '3', '1',
                    '4', '1', '', '', '', '', '', '850000', '', '',
                    '3', '1', '5', '1', 'SI', '0', '0']
        salida = StringIO()
        with patch('main.BaseDatos', return_value=self.base):
            with patch('builtins.input', side_effect=entradas), redirect_stdout(salida):
                self.assertEqual(main(), 0)
        self.assertIn('850000.0', salida.getvalue())
        self.assertIn('Registro eliminado', salida.getvalue())
        self.assertEqual(self.sistema.empleados.listar(), [])

    def test_correo_con_reglas_explicitas(self):
        """Comprueba partes y espacios después de retirar la expresión regular."""
        self.assertEqual(correo('  ana.apellido@ecotech.cl  '), 'ana.apellido@ecotech.cl')
        for valor in ('anaecotech.cl', 'ana@@ecotech.cl', '@ecotech.cl', 'ana@ecotech',
                      'ana@.cl', 'ana@ecotech.', 'ana@eco..cl', 'a na@ecotech.cl',
                      'ana@eco\ttech.cl'):
            with self.subTest(valor=valor):
                with self.assertRaises(DatoInvalidoError):
                    correo(valor)

    def test_formulario_empleado_conserva_y_retira_departamento(self):
        """Enter conserva los datos y '-' retira solo el departamento opcional."""
        dep = self.sistema.departamentos.guardar(Departamento('Contabilidad'))
        empleado = self.nuevo_empleado()
        empleado.departamento_id = dep.id
        self.sistema.empleados.guardar(empleado)
        with patch('builtins.input', side_effect=[''] * 8), redirect_stdout(StringIO()):
            conservado = formulario_empleado(empleado)
        self.assertEqual(conservado.id, empleado.id)
        self.assertEqual(conservado.departamento_id, dep.id)
        self.assertEqual(conservado.salario, 800000)
        with patch('builtins.input', side_effect=[''] * 7 + ['-']), redirect_stdout(StringIO()):
            editado = formulario_empleado(empleado)
        self.sistema.empleados.actualizar(editado)
        self.assertIsNone(self.sistema.empleados.obtener(empleado.id).departamento_id)
        self.assertEqual(empleado.departamento_id, dep.id)

    def test_formularios_proyecto_y_horas_editan_sin_perder_datos(self):
        """El formulario explícito conserva las fechas y la identidad al editar."""
        empleado, proyecto = self.nueva_asignacion()
        with patch('builtins.input', side_effect=['', 'Nueva descripción', '']):
            editado = formulario_proyecto(proyecto)
        self.sistema.proyectos.actualizar(editado)
        self.assertEqual(self.sistema.proyectos.obtener(proyecto.id).descripcion, 'Nueva descripción')
        registro = self.sistema.registros.guardar(RegistroTiempo(
            empleado.id, proyecto.id, '2026-10-22', 4, 'Práctica'))
        with patch('builtins.input', side_effect=['', '', '', '6', '']):
            cambio = formulario_registro(registro)
        self.sistema.registros.actualizar(cambio)
        recuperado = self.sistema.registros.obtener(registro.id)
        self.assertEqual(recuperado.horas, 6)
        self.assertEqual(recuperado.fecha.isoformat(), '2026-10-22')
        self.assertEqual(recuperado.empleado_id, empleado.id)

    def test_mapeo_conserva_todos_los_datos_personales_y_laborales(self):
        """Recuperar una tupla conserva cada campo y su lugar en la consulta."""
        dep = self.sistema.departamentos.guardar(Departamento('Área de prueba'))
        original = Empleado('Lucía', 'Pasaje 22', '00912345678', 'lucia@ecotech.cl',
                            '2025-04-17', 975500, departamento_id=dep.id, rol='gerente')
        self.sistema.empleados.guardar(original)
        recuperado = self.sistema.empleados.obtener(original.id)
        self.assertEqual(recuperado.nombre, 'Lucía')
        self.assertEqual(recuperado.direccion, 'Pasaje 22')
        self.assertEqual(recuperado.telefono, '00912345678')
        self.assertEqual(recuperado.email, 'lucia@ecotech.cl')
        self.assertEqual(recuperado.fecha_inicio.isoformat(), '2025-04-17')
        self.assertEqual(recuperado.salario, 975500)
        self.assertEqual(recuperado.departamento_id, dep.id)
        self.assertEqual(recuperado.rol, 'gerente')


    def test_editar_fecha_respeta_horas_del_dia_destino(self):
        """Cambiar la fecha no permite trasladar horas a un día ya completo."""
        empleado, proyecto = self.nueva_asignacion()
        self.sistema.registros.guardar(RegistroTiempo(
            empleado.id, proyecto.id, '2026-10-22', 24, 'Día completo'))
        registro = self.sistema.registros.guardar(RegistroTiempo(
            empleado.id, proyecto.id, '2026-10-23', 4, 'Otro día'))
        registro.fecha = '2026-10-22'
        with self.assertRaises(RelacionError):
            self.sistema.registros.actualizar(registro)
        self.assertEqual(self.sistema.registros.obtener(registro.id).fecha.isoformat(), '2026-10-23')

    def test_departamento_rechaza_responsable_ajeno(self):
        """La edición directa del departamento comprueba rol y pertenencia."""
        gerente = self.sistema.empleados.guardar(self.nuevo_empleado(rol='gerente'))
        ventas = self.sistema.departamentos.guardar(Departamento('Ventas'))
        self.sistema.asignar_gerente(gerente.id, ventas.id)
        otro = self.sistema.departamentos.guardar(Departamento('Compras'))
        otro.gerente_id = gerente.id
        with self.assertRaises(RelacionError):
            self.sistema.departamentos.actualizar(otro)
        self.assertIsNone(self.sistema.departamentos.obtener(otro.id).gerente_id)

    def test_responsable_no_se_mueve_sin_retirar_responsabilidad(self):
        """Un cambio aislado de empleado no deja al área con un responsable ajeno."""
        gerente = self.sistema.empleados.guardar(self.nuevo_empleado(rol='gerente'))
        ventas = self.sistema.departamentos.guardar(Departamento('Ventas'))
        otro = self.sistema.departamentos.guardar(Departamento('Compras'))
        self.sistema.asignar_gerente(gerente.id, ventas.id)
        gerente.departamento_id = otro.id
        with self.assertRaises(RelacionError):
            self.sistema.empleados.actualizar(gerente)
        self.assertEqual(self.sistema.empleados.obtener(gerente.id).departamento_id, ventas.id)

    def test_actualizar_esquema_anterior_conserva_datos(self):
        """La transición retira un trigger anterior y mantiene los empleados guardados."""
        empleado = self.sistema.empleados.guardar(self.nuevo_empleado())
        with self.base.conexion() as conn:
            conn.execute('''CREATE TRIGGER conservar_responsable BEFORE UPDATE ON empleado
                            BEGIN SELECT RAISE(ABORT, 'Regla anterior'); END''')
        self.base.inicializar()
        recuperado = self.sistema.empleados.obtener(empleado.id)
        recuperado.subir_salario(20000)
        self.sistema.empleados.actualizar(recuperado)
        self.assertEqual(self.sistema.empleados.obtener(empleado.id).salario, 820000)


if __name__ == '__main__':
    unittest.main()
