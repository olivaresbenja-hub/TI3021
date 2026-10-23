"""Menú de consola. Ejecutar: python main.py."""
from dominio.empleado import Empleado
from dominio.departamento import Departamento
from dominio.proyecto import Proyecto
from dominio.registro_tiempo import RegistroTiempo
from repositorio.conexion import BaseDatos
from dominio.excepciones import EcoTechError
from dominio.validaciones import identificador
from dominio.informe_nomina import InformeNomina
from dominio.informe_proyecto import InformeProyecto
from repositorio.sistema_repo import SistemaEcoTech


def leer_id(mensaje="ID: "):
    """Lee y valida el rango entero admitido por SQLite."""
    valor = int(input(mensaje))
    return identificador(valor)


def leer_texto(etiqueta, actual=None):
    """Pide un dato; Enter conserva el anterior durante una edición."""
    if actual is None:
        entrada = input(etiqueta + ": ").strip()
    else:
        entrada = input(etiqueta + " [" + str(actual) + "]: ").strip()
        if entrada == "":
            return actual
    return entrada


def leer_decimal(etiqueta, actual=None):
    """Convierte un número y muestra un mensaje claro si el formato falla."""
    entrada = leer_texto(etiqueta, actual)
    try:
        return float(entrada)
    except ValueError as error:
        raise ValueError(etiqueta + ": formato inválido.") from error


def leer_departamento(actual=None):
    """Lee el ID opcional; '-' retira la asignación al editar."""
    entrada = leer_texto("ID departamento (vacío: sin asignar; -: quitar)", actual)
    if entrada == "" or entrada == "-":
        return None
    return int(entrada)


def formulario_empleado(anterior=None):
    """Construye un empleado nuevo con los datos escritos por el usuario."""
    if anterior is None:
        return Empleado(
            nombre=leer_texto("Nombre"),
            direccion=leer_texto("Dirección"),
            telefono=leer_texto("Teléfono"),
            email=leer_texto("Correo"),
            fecha_inicio=leer_texto("Fecha de inicio AAAA-MM-DD"),
            salario=leer_decimal("Salario"),
            rol=leer_texto("Rol: empleado o gerente"),
            departamento_id=leer_departamento(),
        )
    print("Enter conserva el valor. En departamento, '-' quita la asignación.")
    return Empleado(
        nombre=leer_texto("Nombre", anterior.nombre),
        direccion=leer_texto("Dirección", anterior.direccion),
        telefono=leer_texto("Teléfono", anterior.telefono),
        email=leer_texto("Correo", anterior.email),
        fecha_inicio=leer_texto("Fecha de inicio AAAA-MM-DD", anterior.fecha_inicio),
        salario=leer_decimal("Salario", anterior.salario),
        rol=leer_texto("Rol: empleado o gerente", anterior.rol),
        departamento_id=leer_departamento(anterior.departamento_id),
        id=anterior.id,
    )


def formulario_departamento(anterior=None):
    """Pide el nombre; la responsabilidad se gestiona en Asignaciones."""
    if anterior is None:
        return Departamento(leer_texto("Nombre"))
    return Departamento(
        nombre=leer_texto("Nombre", anterior.nombre),
        gerente_id=anterior.gerente_id,
        id=anterior.id,
    )


def formulario_proyecto(anterior=None):
    """Pide los datos propios del proyecto y conserva el ID al editar."""
    if anterior is None:
        return Proyecto(
            nombre=leer_texto("Nombre"),
            descripcion=leer_texto("Descripción"),
            fecha_inicio=leer_texto("Fecha de inicio AAAA-MM-DD"),
        )
    return Proyecto(
        nombre=leer_texto("Nombre", anterior.nombre),
        descripcion=leer_texto("Descripción", anterior.descripcion),
        fecha_inicio=leer_texto("Fecha de inicio AAAA-MM-DD", anterior.fecha_inicio),
        id=anterior.id,
    )


def formulario_registro(anterior=None):
    """Pide los datos de las horas de un empleado en un proyecto."""
    if anterior is None:
        return RegistroTiempo(
            empleado_id=int(leer_texto("ID empleado")),
            proyecto_id=int(leer_texto("ID proyecto")),
            fecha=leer_texto("Fecha AAAA-MM-DD"),
            horas=leer_decimal("Horas (mayor que 0 y hasta 24)"),
            descripcion=leer_texto("Descripción"),
        )
    return RegistroTiempo(
        empleado_id=int(leer_texto("ID empleado", anterior.empleado_id)),
        proyecto_id=int(leer_texto("ID proyecto", anterior.proyecto_id)),
        fecha=leer_texto("Fecha AAAA-MM-DD", anterior.fecha),
        horas=leer_decimal("Horas (mayor que 0 y hasta 24)", anterior.horas),
        descripcion=leer_texto("Descripción", anterior.descripcion),
        id=anterior.id,
    )


def formulario(entidad, anterior=None):
    """Elige el formulario con condiciones explícitas."""
    if entidad == "empleados":
        return formulario_empleado(anterior)
    if entidad == "departamentos":
        return formulario_departamento(anterior)
    if entidad == "proyectos":
        return formulario_proyecto(anterior)
    if entidad == "registros":
        return formulario_registro(anterior)
    raise ValueError("Entidad desconocida.")


def repositorio_de(sistema, entidad):
    """Selecciona el repositorio sin buscar atributos por un nombre variable."""
    if entidad == "empleados":
        return sistema.empleados
    if entidad == "departamentos":
        return sistema.departamentos
    if entidad == "proyectos":
        return sistema.proyectos
    if entidad == "registros":
        return sistema.registros
    raise ValueError("Entidad desconocida.")


def mostrar_detalle(objeto, entidad):
    """Muestra directamente los atributos de cada entidad."""
    print(objeto)
    if entidad != "registros":
        print("Nombre:", objeto.nombre)
    if entidad == "empleados":
        print("Dirección:", objeto.direccion)
        print("Teléfono:", objeto.telefono)
        print("Correo:", objeto.email)
        print("Fecha de inicio:", objeto.fecha_inicio)
        print("Salario:", objeto.salario)
        print("Rol:", objeto.rol)
        print("ID departamento:", objeto.departamento_id)
    elif entidad == "departamentos":
        print("ID responsable:", objeto.gerente_id)
    elif entidad == "proyectos":
        print("Descripción:", objeto.descripcion)
        print("Fecha de inicio:", objeto.fecha_inicio)
    elif entidad == "registros":
        print("ID empleado:", objeto.empleado_id)
        print("ID proyecto:", objeto.proyecto_id)
        print("Fecha:", objeto.fecha)
        print("Horas:", objeto.horas)
        print("Descripción:", objeto.descripcion)
    print("Consulta las relaciones en la opción Asignaciones del menú principal.")


def menu_entidad(sistema, entidad):
    """Permite el CRUD de una entidad capturando errores de usuario y negocio."""
    repo = repositorio_de(sistema, entidad)
    while True:
        print(f"\n--- {entidad.upper()} ---")
        print("1 Crear | 2 Listar/buscar | 3 Consultar ID | 4 Editar | 5 Eliminar | 0 Volver")
        opcion = input("Opción: ").strip()
        try:
            if opcion == "0":
                return
            if opcion == "1":
                objeto = repo.guardar(formulario(entidad))
                print(f"Guardado con ID {objeto.id}.")
            elif opcion == "2":
                busqueda = input("Buscar texto (Enter: todos): ")
                objetos = repo.buscar(busqueda) if busqueda else repo.listar()
                for objeto in objetos:
                    print(objeto)
                print(f"Total: {len(objetos)}")
            elif opcion in ("3", "4", "5"):
                id = leer_id()
                objeto = repo.obtener(id)
                if objeto is None:
                    print("No existe un registro con ese ID.")
                    continue
                if opcion == "3":
                    mostrar_detalle(objeto, entidad)
                elif opcion == "4":
                    repo.actualizar(formulario(entidad, objeto))
                    print("Cambios guardados.")
                elif input(f"Eliminar {objeto}? Escribe SI: ").strip() == "SI":
                    repo.eliminar(id)
                    print("Registro eliminado.")
                else:
                    print("Eliminación cancelada.")
            else:
                print("Opción inválida.")
        except (ValueError, EcoTechError) as exc:
            print(f"No se completó la operación: {exc}")


def menu_relaciones(sistema):
    """Permite asignar y retirar relaciones guardadas en la base."""
    while True:
        print("\n--- ASIGNACIONES ---")
        print("1 Asignar empleado a proyecto | 2 Quitar asignación | 3 Ver asignaciones")
        print("4 Asignar gerente a departamento | 5 Quitar gerente | 0 Volver")
        opcion = input("Opción: ").strip()
        try:
            if opcion == "0":
                return
            if opcion in ("1", "2"):
                empleado_id = leer_id("ID empleado: ")
                proyecto_id = leer_id("ID proyecto: ")
                if opcion == "1":
                    sistema.vincular(empleado_id, proyecto_id)
                else:
                    sistema.desvincular(empleado_id, proyecto_id)
                print("Asignación actualizada.")
            elif opcion == "3":
                filas = sistema.relaciones()
                for empleado_id, nombre, proyecto_id, proyecto in filas:
                    print(f"Empleado {empleado_id}: {nombre}",
                          f"-> Proyecto {proyecto_id}: {proyecto}")
                if not filas:
                    print("No hay asignaciones.")
            elif opcion == "4":
                gerente_id = leer_id("ID gerente: ")
                departamento_id = leer_id("ID departamento: ")
                sistema.asignar_gerente(gerente_id, departamento_id)
                print("Responsable asignado.")
            elif opcion == "5":
                sistema.quitar_gerente(leer_id("ID departamento: "))
                print("Responsabilidad retirada.")
            else:
                print("Opción inválida.")
        except (ValueError, EcoTechError) as exc:
            print(f"No se completó la operación: {exc}")



def mostrar_informes(sistema):
    """Procesa una lista mixta usando el mismo método, sin condicionales por tipo."""
    informes = [InformeNomina(sistema.empleados.listar())]
    registros = sistema.registros.listar()
    for proyecto in sistema.proyectos.listar():
        informes.append(InformeProyecto(proyecto, registros))
    for informe in informes:
        print(informe.exportar())


def contratar(sistema):
    """Expone en consola una operación real de dos escrituras atómicas."""
    try:
        print('Crear empleado y asignarlo a un proyecto existente en una sola operación.')
        empleado = formulario('empleados')
        proyecto_id = leer_id('ID proyecto: ')
        sistema.contratar_en_proyecto(empleado, proyecto_id)
        print('Empleado y asignación guardados con ID', empleado.id)
    except (ValueError, EcoTechError) as error:
        print('No se guardó la contratación:', error)


def main():
    """Inicia la base, presenta el menú y permite cerrar sin perder confirmaciones."""
    try:
        base = BaseDatos()
        base.inicializar()
        sistema = SistemaEcoTech(base)
        while True:
            print("\nECOTECH SOLUTIONS")
            print("1 Empleados y roles | 2 Departamentos | 3 Proyectos")
            print("4 Registros de horas | 5 Asignaciones | 6 Informes")
            print("7 Contratar en proyecto | 0 Salir")
            opcion = input("Opción: ").strip()
            if opcion == "0":
                print("Hasta luego.")
                return 0
            elif opcion == "5":
                menu_relaciones(sistema)
            elif opcion == "6":
                mostrar_informes(sistema)
            elif opcion == "7":
                contratar(sistema)
            elif opcion in ("1", "2", "3", "4"):
                entidades = {"1": "empleados", "2": "departamentos",
                             "3": "proyectos", "4": "registros"}
                menu_entidad(sistema, entidades[opcion])
            else:
                print("Opción inválida.")
    except EcoTechError as exc:
        print(f"No se pudo iniciar: {exc}")
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nSesión terminada. Las operaciones ya confirmadas están guardadas.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
