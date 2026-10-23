"""CRUD de Departamento: cada operación se lee completa en este archivo."""
from dominio.departamento import Departamento
from dominio.validaciones import identificador
from dominio.excepciones import DatoInvalidoError, RegistroNoEncontradoError, RelacionError


class DepartamentoRepositorio:
    """Guarda y recupera Departamento utilizando la conexión compartida."""

    SQL_INSERTAR = (
        'INSERT INTO departamento (nombre, gerente_id) VALUES (?, ?)'
    )

    SQL_OBTENER = (
        'SELECT id, nombre, gerente_id FROM departamento WHERE id = ?'
    )

    SQL_LISTAR = (
        'SELECT id, nombre, gerente_id FROM departamento ORDER BY id'
    )

    SQL_BUSCAR = (
        'SELECT id, nombre, gerente_id FROM departamento WHERE '
        'instr(lower(nombre), lower(?)) > 0 ORDER BY id'
    )

    SQL_ACTUALIZAR = (
        'UPDATE departamento SET nombre = ?, gerente_id = ? WHERE id = ?'
    )

    SQL_ELIMINAR = (
        'DELETE FROM departamento WHERE id = ?'
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
            self._validar_responsable(conn, objeto)
            cursor = conn.execute(self.SQL_INSERTAR, valores)
            nuevo_id = cursor.lastrowid
        objeto.id = nuevo_id
        return objeto

    def actualizar(self, objeto):
        """Guarda los atributos de una entidad existente."""
        identificador(objeto.id)
        valores = self.valores(objeto)
        with self.base.conexion() as conn:
            self._validar_responsable(conn, objeto)
            cursor = conn.execute(self.SQL_ACTUALIZAR, valores + (objeto.id,))
            if cursor.rowcount == 0:
                raise RegistroNoEncontradoError('No existe el registro que quieres editar.')
        return objeto

    def _validar_responsable(self, conn, departamento):
        """Comprueba el rol y la pertenencia del responsable indicado."""
        if departamento.gerente_id is None:
            return
        empleado = conn.execute(
            'SELECT rol, departamento_id FROM empleado WHERE id = ?',
            (departamento.gerente_id,),
        ).fetchone()
        if empleado is None:
            raise RelacionError('El responsable no existe.')
        if empleado[0] != 'gerente' or empleado[1] != departamento.id:
            raise RelacionError('El responsable debe ser gerente y pertenecer al departamento.')

    def _a_objeto(self, fila) -> Departamento:
        """Mapper centralizado: reconstruye y valida una fila."""
        return Departamento(
            nombre=fila[1],
            gerente_id=fila[2],
            id=fila[0],
        )

    def valores(self, objeto: Departamento) -> tuple:
        """Vuelve a validar atributos antes de escribirlos en SQLite."""
        valido = Departamento(
            nombre=objeto.nombre,
            gerente_id=objeto.gerente_id,
            id=objeto.id,
        )
        return (
            valido.nombre,
            valido.gerente_id,
        )
