"""Pruebas demostrativas reproducibles sin modificar la base del menú."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse
import html

from dominio.empleado import Empleado
from dominio.departamento import Departamento
from dominio.proyecto import Proyecto
from dominio.registro_tiempo import RegistroTiempo
from dominio.excepciones import RelacionError, DatoInvalidoError
from dominio.informe_nomina import InformeNomina
from dominio.informe_proyecto import InformeProyecto
from repositorio.conexion import BaseDatos
from repositorio.sistema_repo import SistemaEcoTech

RAIZ = Path(__file__).resolve().parent


def empleado(nombre: str, email: str) -> Empleado:
    """Construye datos ficticios para la demostración."""
    return Empleado(nombre, 'Dirección de ejemplo', '912345678', email,
                    '2026-10-01', 850000)


def probar_sql(sistema):
    """Muestra el payload exigido y comprueba que no devuelve toda la tabla."""
    print('PRUEBA DE CONSULTA PARAMETRIZADA')
    sistema.empleados.guardar(empleado('Ana', 'ana@ecotech.cl'))
    sistema.empleados.guardar(empleado('Diego', 'diego@ecotech.cl'))
    print('Empleados existentes:', len(sistema.empleados.listar()))
    print('Consulta SQL real:')
    print(sistema.empleados.SQL_BUSCAR)
    ataque = "' OR '1'='1"
    print('Parámetro enviado por separado:', repr(ataque))
    resultados = sistema.empleados.buscar(ataque)
    print('Resultado de buscar el payload:', resultados)
    print('Filas devueltas:', len(resultados))
    assert resultados == []
    assert len(sistema.empleados.listar()) == 2
    print('COMPROBADO: la entrada se interpreta como texto, no como SQL.')


def probar_rollback(sistema):
    """Fuerza el fallo de la segunda escritura de una contratación real."""
    print('PRUEBA DE TRANSACCIÓN ATÓMICA')
    nuevo = empleado('Prueba rollback', 'rollback@ecotech.cl')
    antes = len(sistema.empleados.listar())
    print('Empleados antes:', antes)
    print('Primera escritura: INSERT del empleado.')
    print('Segunda escritura: INSERT de asignación al proyecto inexistente 999.')
    try:
        sistema.contratar_en_proyecto(nuevo, 999)
    except RelacionError as error:
        print('Error capturado:', type(error).__name__)
        print(error)
    else:
        raise AssertionError('La segunda escritura debía fallar.')
    despues = len(sistema.empleados.listar())
    print('Empleados después del rollback:', despues)
    print('ID del objeto tras el fallo:', nuevo.id)
    print('Asignaciones después:', sistema.relaciones())
    assert antes == despues and nuevo.id is None
    assert sistema.relaciones() == []
    print('COMPROBADO: la primera escritura también se revirtió.')


def probar_crud(sistema):
    """Demuestra CRUD, rol modificable y una colección polimórfica."""
    print('DEMOSTRACIÓN COMPLETA ECOTECH')
    dep = sistema.departamentos.guardar(Departamento('Contabilidad'))
    proyecto = sistema.proyectos.guardar(Proyecto('Panel Solar', 'Horas del equipo', '2026-10-01'))
    ana = empleado('Ana', 'ana@ecotech.cl')
    ana.asignar_departamento(dep)
    sistema.contratar_en_proyecto(ana, proyecto.id)
    print('CREAR:', ana)
    print('LEER:', sistema.empleados.obtener(ana.id))
    ana.subir_salario(50000)
    sistema.empleados.actualizar(ana)
    print('ACTUALIZAR:', sistema.empleados.obtener(ana.id))
    registro = sistema.registros.guardar(RegistroTiempo(
        ana.id, proyecto.id, '2026-10-22', 4, 'Pruebas del proyecto'))
    print('POLIMORFISMO:')
    informes = [InformeNomina(sistema.empleados.listar()),
                InformeProyecto(proyecto, sistema.registros.listar())]
    for informe in informes:
        print(informe.exportar())
    ana.rol = 'gerente'
    sistema.empleados.actualizar(ana)
    sistema.asignar_gerente(ana.id, dep.id)
    print('ROL: misma clase', type(ana).__name__, '; mismo ID', ana.id, '; rol', ana.rol)
    try:
        sistema.empleados.obtener(10 ** 30)
    except DatoInvalidoError as error:
        print('ID FUERA DE RANGO CONTROLADO:', error)
    sistema.quitar_gerente(dep.id)
    sistema.registros.eliminar(registro.id)
    sistema.empleados.eliminar(ana.id)
    print('ELIMINAR:', sistema.empleados.obtener(ana.id))


def ejecutar(caso: str, guardar: bool = False):
    """Captura la salida real para adjuntar evidencias, claramente identificadas."""
    salida = StringIO()
    with TemporaryDirectory(dir=RAIZ / 'tests') as carpeta:
        base = BaseDatos(Path(carpeta) / 'demo.db')
        base.inicializar()
        sistema = SistemaEcoTech(base)
        with redirect_stdout(salida):
            if caso == 'sql':
                probar_sql(sistema)
            elif caso == 'rollback':
                probar_rollback(sistema)
            else:
                probar_crud(sistema)
    contenido = salida.getvalue()
    print(contenido, end='')
    if guardar:
        carpeta = RAIZ / 'evidencias'
        carpeta.mkdir(exist_ok=True)
        (carpeta / (caso + '.txt')).write_text(contenido, encoding='utf-8')
        pagina = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                  '<title>EcoTech evidencia de ejecución</title>'
                  '<style>body{font:18px Arial;margin:32px;color:#17212b;max-width:1100px}'
                  'pre{font:16px/1.6 Consolas,monospace;white-space:pre-wrap;'
                  'background:#f1f4f7;padding:24px;border:1px solid #c4ced8}'
                  'p{font-size:16px}</style><h1>EcoTech ES2</h1>'
                  '<p>Prueba automatizada de demo.py con asistencia de IA. '
                  'Datos ficticios y base temporal.</p><pre>'
                  + html.escape(contenido) + '</pre>'
                  '<p>EcoTech ES2 — registro reproducible de verificación técnica.</p></html>')
        (carpeta / (caso + '.html')).write_text(pagina, encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--caso', choices=['sql', 'rollback', 'crud'], default='crud')
    parser.add_argument('--guardar', action='store_true')
    opciones = parser.parse_args()
    ejecutar(opciones.caso, opciones.guardar)
