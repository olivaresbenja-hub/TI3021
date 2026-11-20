"""Integra el clima y la conversión salarial con proyectos de EcoTech."""
from datetime import datetime, timezone

from api_cliente import ServicioNoDisponible
from dominio.excepciones import EcoTechError
from servicios_externos import (
    buscar_ciudades, consultar_clima, consultar_cotizacion, convertir_salario,
    describir_clima, describir_cotizacion, validar_moneda, validar_ubicacion,
)


def elegir_proyecto(sistema, leer_id):
    proyectos = sistema.proyectos.listar()
    if not proyectos:
        raise EcoTechError('Crea un proyecto desde el menú principal.')
    for proyecto in proyectos:
        print(f'{proyecto.id} {proyecto.nombre}')
    proyecto = sistema.proyectos.obtener(leer_id('ID del proyecto: '))
    if proyecto is None:
        raise EcoTechError('El proyecto no existe.')
    return proyecto


def elegir_clima(ciudad, pais, leer_id):
    lugares = buscar_ciudades(ciudad, pais)
    for posicion, lugar in enumerate(lugares, 1):
        print(f'{posicion} {lugar[0]}')
    seleccion = leer_id('Número de la ubicación: ')
    if seleccion > len(lugares):
        raise EcoTechError('Selecciona una ubicación de la lista.')
    return consultar_clima(lugares[seleccion - 1])


def consultar_con_respaldo(sistema, proyecto, tipo, clave, consultar):
    try:
        datos = consultar()
    except ServicioNoDisponible as error:
        respaldo = sistema.obtener_dato_externo(proyecto.id, tipo, clave)
        if respaldo is None:
            raise EcoTechError(f'{error} Todavía no hay datos guardados para esta consulta.') from None
        obtenido_en, datos = respaldo
        antiguedad = datetime.now(timezone.utc) - datetime.fromisoformat(obtenido_en)
        minutos = max(0, int(antiguedad.total_seconds() // 60))
        print(f'{error} Plan B: dato guardado hace {minutos} min. obtenido_en: {obtenido_en}')
        return datos
    obtenido_en = sistema.guardar_dato_externo(proyecto.id, tipo, clave, datos)
    print(f'Dato actualizado en SQLite. obtenido_en: {obtenido_en}')
    return datos


def clima(sistema, proyecto, leer_id):
    ciudad, pais = validar_ubicacion(input('Ciudad: '), input('País (por ejemplo CL): '))
    datos = consultar_con_respaldo(
        sistema, proyecto, 'clima', f'{pais}:{ciudad.casefold()}',
        lambda: elegir_clima(ciudad, pais, leer_id),
    )
    return describir_clima(datos)


def conversion(sistema, proyecto, leer_id):
    filas = sistema.empleados_por_proyecto(proyecto.id)
    if not filas:
        raise EcoTechError('Asigna al menos un empleado al proyecto desde el menú principal.')
    empleados = {id_empleado: (nombre, salario) for id_empleado, nombre, salario in filas}
    for id_empleado, (nombre, _) in empleados.items():
        print(f'{id_empleado} {nombre}')
    elegido = leer_id('ID del empleado asignado: ')
    if elegido not in empleados:
        raise EcoTechError('El empleado seleccionado no está asignado al proyecto.')
    _, salario = empleados[elegido]
    moneda = validar_moneda(input('Moneda (USD/EUR): '))
    datos = consultar_con_respaldo(
        sistema, proyecto, 'cotización', moneda, lambda: consultar_cotizacion(moneda),
    )
    resultado = convertir_salario(salario, datos)
    return f'Empleado ID {elegido} | {resultado}'


def mostrar_historial(sistema):
    filas = sistema.consultas_externas_recientes()
    if not filas:
        print('Todavía no hay consultas guardadas.')
    for fecha, proyecto, tipo, datos in filas:
        resultado = describir_clima(datos) if tipo == 'clima' else describir_cotizacion(datos)
        print(f'{fecha} | {proyecto} | {tipo} | {resultado}')


def menu_servicios(sistema, leer_id):
    while True:
        print('\n1 Clima del proyecto | 2 Estimar salario en otra moneda')
        print('3 Datos guardados (últimos 15 respaldos) | 0 Volver')
        opcion = input('Opción: ').strip()
        try:
            if opcion == '0':
                return
            if opcion == '3':
                mostrar_historial(sistema)
                continue
            if opcion not in ('1', '2'):
                print('Opción inválida.')
                continue
            proyecto = elegir_proyecto(sistema, leer_id)
            if opcion == '1':
                resultado = clima(sistema, proyecto, leer_id)
            else:
                resultado = conversion(sistema, proyecto, leer_id)
            print(f'{proyecto.nombre} | {resultado}')
        except (EcoTechError, ValueError) as error:
            print(f'No se completó la consulta: {error}')
