"""CRUD de Empleado: cada operación se lee completa en este archivo."""
from dominio.empleado import Empleado
from dominio.validaciones import identificador
from dominio.excepciones import DatoInvalidoError, RegistroNoEncontradoError, RelacionError


class EmpleadoRepositorio:
    """Guarda y recupera Empleado utilizando la conexión compartida."""

    SQL_INSERTAR = (
        'INSERT INTO empleado (nombre, direccion, telefono, email, fecha_inicio, '
        'salario, departamento_id, rol) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
    )

    SQL_OBTENER = (
        'SELECT id, nombre, direccion, telefono, email, fecha_inicio, salario, '
        'departamento_id, rol FROM empleado WHERE id = ?'
    )

    SQL_LISTAR = (
        'SELECT id, nombre, direccion, telefono, email, fecha_inicio, salario, '
        'departamento_id, rol FROM empleado ORDER BY id'
    )

    SQL_BUSCAR = (
        'SELECT id, nombre, direccion, telefono, email, fecha_inicio, salario, '
        'departamento_id, rol FROM empleado WHERE instr(lower(nombre), lower(?)) > '
        '0 ORDER BY id'
    )

    SQL_ACTUALIZAR = (
        'UPDATE empleado SET nombre = ?, direccion = ?, telefono = ?, email = ?, '
        'fecha_inicio = ?, salario = ?, departamento_id = ?, rol = ? WHERE id = ?'
    )

    SQL_ELIMINAR = (
        'DELETE FROM empleado WHERE id = ?'
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

    def guardar_en_conexion(self, conn, objeto: Empleado) -> int:
        """Inserta usando la conexión recibida, sin confirmar por separado."""
        if objeto.id is not None:
            raise DatoInvalidoError('El objeto ya tiene ID; utiliza actualizar.')
        valores = self.valores(objeto)
        cursor = conn.execute(self.SQL_INSERTAR, valores)
        return cursor.lastrowid

    def guardar(self, objeto: Empleado):
        """Asigna el ID al objeto después de confirmar la inserción."""
        with self.base.conexion() as conn:
            nuevo_id = self.guardar_en_conexion(conn, objeto)
        objeto.id = nuevo_id
        return objeto

    def actualizar(self, objeto):
        """Guarda los atributos de una entidad existente."""
        identificador(objeto.id)
        valores = self.valores(objeto)
        with self.base.conexion() as conn:
            self._validar_responsabilidad(conn, objeto)
            cursor = conn.execute(self.SQL_ACTUALIZAR, valores + (objeto.id,))
            if cursor.rowcount == 0:
                raise RegistroNoEncontradoError('No existe el registro que quieres editar.')
        return objeto

    def _validar_responsabilidad(self, conn, empleado):
        """Un responsable debe conservar su rol y el departamento que dirige."""
        departamento = conn.execute(
            'SELECT id FROM departamento WHERE gerente_id = ?', (empleado.id,)
        ).fetchone()
        if departamento is not None:
            if empleado.rol != 'gerente' or empleado.departamento_id != departamento[0]:
                raise RelacionError('Retira primero la responsabilidad del departamento.')

    def _a_objeto(self, fila) -> Empleado:
        """Mapper centralizado: reconstruye y valida una fila."""
        return Empleado(
            nombre=fila[1],
            direccion=fila[2],
            telefono=fila[3],
            email=fila[4],
            fecha_inicio=fila[5],
            salario=fila[6],
            departamento_id=fila[7],
            rol=fila[8],
            id=fila[0],
        )

    def valores(self, objeto: Empleado) -> tuple:
        """Vuelve a validar atributos antes de escribirlos en SQLite."""
        valido = Empleado(
            nombre=objeto.nombre,
            direccion=objeto.direccion,
            telefono=objeto.telefono,
            email=objeto.email,
            fecha_inicio=objeto.fecha_inicio,
            salario=objeto.salario,
            departamento_id=objeto.departamento_id,
            rol=objeto.rol,
            id=objeto.id,
        )
        return (
            valido.nombre,
            valido.direccion,
            valido.telefono,
            valido.email,
            valido.fecha_inicio.isoformat(),
            valido.salario,
            valido.departamento_id,
            valido.rol,
        )
