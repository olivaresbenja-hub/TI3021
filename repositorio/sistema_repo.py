"""Repositorio coordinador de relaciones y operaciones de varias escrituras."""
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
