"""CRUD de RegistroTiempo: cada operación se lee completa en este archivo."""
from dominio.registro_tiempo import RegistroTiempo
from dominio.validaciones import identificador, fecha
from dominio.excepciones import DatoInvalidoError, RegistroNoEncontradoError, RelacionError


class RegistroTiempoRepositorio:
    """Guarda y recupera RegistroTiempo utilizando la conexión compartida."""

    SQL_INSERTAR = (
        'INSERT INTO registro_tiempo (empleado_id, proyecto_id, fecha, horas, '
        'descripcion) VALUES (?, ?, ?, ?, ?)'
    )

    SQL_OBTENER = (
        'SELECT id, empleado_id, proyecto_id, fecha, horas, descripcion FROM '
        'registro_tiempo WHERE id = ?'
    )

    SQL_LISTAR = (
        'SELECT id, empleado_id, proyecto_id, fecha, horas, descripcion FROM '
        'registro_tiempo ORDER BY id'
    )

    SQL_BUSCAR = (
        'SELECT id, empleado_id, proyecto_id, fecha, horas, descripcion FROM '
        'registro_tiempo WHERE instr(lower(descripcion), lower(?)) > 0 ORDER BY id'
    )

    SQL_ACTUALIZAR = (
        'UPDATE registro_tiempo SET empleado_id = ?, proyecto_id = ?, fecha = ?, '
        'horas = ?, descripcion = ? WHERE id = ?'
    )

    SQL_ELIMINAR = (
        'DELETE FROM registro_tiempo WHERE id = ?'
    )

    def __init__(self, base):
        self.base = base

    def obtener(self, id: int):
        """Consulta un ID; devuelve un objeto o None si no existe."""
        identificador(id)
        with self.base.conexion() as conn:
            fila = conn.execute(self.SQL_OBTENER, (id,)).fetchone()
        if fila is None:
            return None
        return self._a_objeto(fila)

    def listar(self) -> list:
        """Convierte todas las filas en objetos del dominio."""
        with self.base.conexion() as conn:
            filas = conn.execute(self.SQL_LISTAR).fetchall()
        objetos = []
        for fila in filas:
            objetos.append(self._a_objeto(fila))
        return objetos

    def buscar(self, texto: str) -> list:
        """El texto se envía como parámetro separado de la consulta."""
        with self.base.conexion() as conn:
            filas = conn.execute(self.SQL_BUSCAR, (texto,)).fetchall()
        objetos = []
        for fila in filas:
            objetos.append(self._a_objeto(fila))
        return objetos

    def eliminar(self, id: int):
        """Elimina una fila si sus relaciones lo permiten."""
        identificador(id)
        with self.base.conexion() as conn:
            cursor = conn.execute(self.SQL_ELIMINAR, (id,))
            if cursor.rowcount == 0:
                raise RegistroNoEncontradoError('No existe el registro que quieres eliminar.')

    def guardar(self, objeto):
        """Valida, inserta y asigna el ID después de confirmar."""
        if objeto.id is not None:
            raise DatoInvalidoError('El objeto ya tiene ID; utiliza actualizar.')
        valores = self.valores(objeto)
        with self.base.conexion() as conn:
            self._validar_horas_diarias(conn, objeto)
            cursor = conn.execute(self.SQL_INSERTAR, valores)
            nuevo_id = cursor.lastrowid
        objeto.id = nuevo_id
        return objeto

    def actualizar(self, objeto):
        """Guarda los atributos de una entidad existente."""
        identificador(objeto.id)
        valores = self.valores(objeto)
        with self.base.conexion() as conn:
            self._validar_horas_diarias(conn, objeto)
            cursor = conn.execute(self.SQL_ACTUALIZAR, valores + (objeto.id,))
            if cursor.rowcount == 0:
                raise RegistroNoEncontradoError('No existe el registro que quieres editar.')
        return objeto

    def _validar_horas_diarias(self, conn, registro):
        """Consulta las otras horas del empleado antes de guardar o editar."""
        dia = fecha(registro.fecha).isoformat()
        if registro.id is None:
            fila = conn.execute(
                'SELECT SUM(horas) FROM registro_tiempo WHERE empleado_id = ? AND fecha = ?',
                (registro.empleado_id, dia),
            ).fetchone()
        else:
            fila = conn.execute(
                'SELECT SUM(horas) FROM registro_tiempo WHERE empleado_id = ? AND fecha = ? AND id != ?',
                (registro.empleado_id, dia, registro.id),
            ).fetchone()
        total = fila[0]
        if total is None:
            total = 0
        if total + registro.horas > 24:
            raise RelacionError('El total diario supera 24 horas.')

    def _a_objeto(self, fila) -> RegistroTiempo:
        """Mapper centralizado: reconstruye y valida una fila."""
        return RegistroTiempo(
            empleado_id=fila[1],
            proyecto_id=fila[2],
            fecha=fila[3],
            horas=fila[4],
            descripcion=fila[5],
            id=fila[0],
        )

    def valores(self, objeto: RegistroTiempo) -> tuple:
        """Vuelve a validar atributos antes de escribirlos en SQLite."""
        valido = RegistroTiempo(
            empleado_id=objeto.empleado_id,
            proyecto_id=objeto.proyecto_id,
            fecha=objeto.fecha,
            horas=objeto.horas,
            descripcion=objeto.descripcion,
            id=objeto.id,
        )
        return (
            valido.empleado_id,
            valido.proyecto_id,
            valido.fecha.isoformat(),
            valido.horas,
            valido.descripcion,
        )
