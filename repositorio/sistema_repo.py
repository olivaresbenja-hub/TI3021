"""Repositorio coordinador de relaciones y operaciones de varias escrituras."""
from datetime import datetime, timezone
import json

from dominio.empleado import Empleado
from dominio.excepciones import RelacionError, RegistroNoEncontradoError
from dominio.validaciones import identificador
from repositorio.empleado_repo import EmpleadoRepositorio
from repositorio.departamento_repo import DepartamentoRepositorio
from repositorio.proyecto_repo import ProyectoRepositorio
from repositorio.registro_tiempo_repo import RegistroTiempoRepositorio


class SistemaEcoTech:
    """Ofrece las operaciones completas que utiliza el menú."""

    def __init__(self, base):
        """Comparte una configuración de base entre los repositorios."""
        self.base = base
        self.empleados = EmpleadoRepositorio(base)
        self.departamentos = DepartamentoRepositorio(base)
        self.proyectos = ProyectoRepositorio(base)
        self.registros = RegistroTiempoRepositorio(base)

    def vincular(self, empleado_id: int, proyecto_id: int):
        """Guarda inmediatamente la asignación; no deja un cambio solo en memoria."""
        identificador(empleado_id)
        identificador(proyecto_id)
        if not self.empleados.obtener(empleado_id) or not self.proyectos.obtener(proyecto_id):
            raise RegistroNoEncontradoError('Empleado o proyecto inexistente.')
        with self.base.conexion() as conn:
            conn.execute(
                'INSERT INTO empleado_proyecto (empleado_id, proyecto_id) VALUES (?, ?)',
                (empleado_id, proyecto_id),
            )

    def desvincular(self, empleado_id: int, proyecto_id: int):
        """Elimina la asignación si no existen horas que dependan de ella."""
        identificador(empleado_id)
        identificador(proyecto_id)
        with self.base.conexion() as conn:
            cursor = conn.execute(
                'DELETE FROM empleado_proyecto WHERE empleado_id = ? AND proyecto_id = ?',
                (empleado_id, proyecto_id),
            )
            if not cursor.rowcount:
                raise RegistroNoEncontradoError('La asignación no existe.')

    def relaciones(self) -> list:
        """Devuelve nombres e IDs para consultar asignaciones en el menú."""
        with self.base.conexion() as conn:
            filas = conn.execute(
                'SELECT e.id, e.nombre, p.id, p.nombre FROM empleado_proyecto ep '
                'JOIN empleado e ON e.id = ep.empleado_id '
                'JOIN proyecto p ON p.id = ep.proyecto_id ORDER BY e.id, p.id'
            ).fetchall()
        return filas

    def empleados_por_proyecto(self, proyecto_id: int) -> list:
        """Obtiene los datos necesarios para estimar el salario de un asignado."""
        identificador(proyecto_id)
        with self.base.conexion() as conn:
            return conn.execute(
                'SELECT e.id, e.nombre, e.salario FROM empleado e '
                'JOIN empleado_proyecto ep ON ep.empleado_id = e.id '
                'WHERE ep.proyecto_id = ? ORDER BY e.id',
                (proyecto_id,),
            ).fetchall()

    def guardar_dato_externo(self, proyecto_id, tipo, clave, datos):
        """Actualiza la última respuesta válida para la misma consulta."""
        obtenido_en = datetime.now(timezone.utc).isoformat(timespec='seconds')
        with self.base.conexion() as conn:
            conn.execute(
                'INSERT INTO dato_externo (proyecto_id, tipo, clave, obtenido_en, datos) '
                'VALUES (?, ?, ?, ?, ?) ON CONFLICT (proyecto_id, tipo, clave) DO UPDATE '
                'SET obtenido_en = excluded.obtenido_en, datos = excluded.datos',
                (proyecto_id, tipo, clave, obtenido_en, json.dumps(datos, ensure_ascii=False)),
            )
        return obtenido_en

    def obtener_dato_externo(self, proyecto_id, tipo, clave):
        with self.base.conexion() as conn:
            fila = conn.execute(
                'SELECT obtenido_en, datos FROM dato_externo WHERE proyecto_id = ? AND tipo = ? AND clave = ?',
                (proyecto_id, tipo, clave),
            ).fetchone()
        if fila is None:
            return None
        obtenido_en, datos = fila
        return obtenido_en, json.loads(datos)

    def consultas_externas_recientes(self) -> list:
        """Recupera los 15 respaldos más recientes para el menú."""
        with self.base.conexion() as conn:
            filas = conn.execute(
                'SELECT d.obtenido_en, p.nombre, d.tipo, d.datos FROM dato_externo d '
                'JOIN proyecto p ON p.id = d.proyecto_id ORDER BY d.obtenido_en DESC LIMIT 15'
            ).fetchall()
        return [(fecha, proyecto, tipo, json.loads(datos)) for fecha, proyecto, tipo, datos in filas]

    def asignar_gerente(self, empleado_id: int, departamento_id: int):
        """Mueve a un empleado con rol gerente y asigna su responsabilidad atómicamente."""
        empleado = self.empleados.obtener(empleado_id)
        departamento = self.departamentos.obtener(departamento_id)
        if not empleado or not departamento:
            raise RegistroNoEncontradoError('Empleado o departamento inexistente.')
        if empleado.rol != 'gerente':
            raise RelacionError('El empleado debe tener rol gerente.')
        with self.base.conexion() as conn:
            conn.execute(
                'UPDATE departamento SET gerente_id = NULL WHERE gerente_id = ?',
                (empleado_id,),
            )
            conn.execute(
                'UPDATE empleado SET departamento_id = ? WHERE id = ?',
                (departamento_id, empleado_id),
            )
            conn.execute(
                'UPDATE departamento SET gerente_id = ? WHERE id = ?',
                (empleado_id, departamento_id),
            )

    def quitar_gerente(self, departamento_id: int):
        """Retira una responsabilidad sin eliminar al empleado."""
        identificador(departamento_id)
        with self.base.conexion() as conn:
            cursor = conn.execute(
                'UPDATE departamento SET gerente_id = NULL WHERE id = ?',
                (departamento_id,),
            )
            if not cursor.rowcount:
                raise RegistroNoEncontradoError('El departamento no existe.')

    def contratar_en_proyecto(self, empleado: Empleado, proyecto_id: int):
        """Inserta empleado y asignación en la misma transacción, todo o nada."""
        identificador(proyecto_id)
        with self.base.conexion() as conn:
            nuevo_id = self.empleados.guardar_en_conexion(conn, empleado)
            conn.execute(
                'INSERT INTO empleado_proyecto (empleado_id, proyecto_id) VALUES (?, ?)',
                (nuevo_id, proyecto_id),
            )
        # Si falla la segunda escritura, no se asigna al objeto un ID inexistente.
        empleado.id = nuevo_id
        return empleado
