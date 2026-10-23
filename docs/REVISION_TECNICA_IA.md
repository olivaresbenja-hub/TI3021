# Revisión técnica del código asistido por IA

Los siguientes fragmentos pertenecen al código que se entrega. Se identifican el apoyo de IA, las decisiones técnicas y las comprobaciones realizadas durante la revisión.

## 1. Consultas parametrizadas

Decisión: **Modifico**. Se sustituyó la construcción dinámica de la estructura SQL por sentencias literales completas. Los valores se envían por separado. La corrección elimina la construcción dinámica y conserva la parametrización de los datos.

Archivo: `repositorio/empleado_repo.py`.

```python
    def buscar(self, texto: str) -> list:
        """El texto se envía como parámetro separado de la consulta."""
        with self.base.conexion() as conn:
            filas = conn.execute(self.SQL_BUSCAR, (texto,)).fetchall()
        objetos = []
        for fila in filas:
            objetos.append(self._a_objeto(fila))
        return objetos
```

Comprobación: test_sql_no_se_construye_en_tiempo_de_ejecucion y demo.py --caso sql. La búsqueda recibe la entrada de ataque como texto y conserva los registros.

## 2. Rango de identificadores

Decisión: **Modifico**. Se incorporó el máximo entero admitido por SQLite para impedir OverflowError y conservar el control del menú.

Archivo: `dominio/validaciones.py`.

```python
def identificador(valor: int, opcional: bool = False) -> int:
    """Impide IDs nulos obligatorios y enteros fuera del rango de SQLite."""
    if valor is None and opcional:
        return None
    if type(valor) is not int or not 1 <= valor <= MAX_ID:
        raise DatoInvalidoError('El ID debe estar entre 1 y 9223372036854775807.')
    return valor
```

Comprobación: Consulta desde el menú con texto, cero, negativo y enteros fuera de rango: cinco errores controlados y salida normal.

## 3. Organización del CRUD

Decisión: **Modifico**. Las operaciones se concentran por entidad para seguir su recorrido completo. Se comparten conexión, validaciones y clases del dominio.

Archivo: `repositorio/empleado_repo.py`.

```python
    def guardar(self, objeto: Empleado):
        """Asigna el ID al objeto después de confirmar la inserción."""
        with self.base.conexion() as conn:
            nuevo_id = self.guardar_en_conexion(conn, objeto)
        objeto.id = nuevo_id
        return objeto
```

Comprobación: CRUD de las cuatro entidades y recuperación en otro proceso, sin asignar un ID antes de confirmar.

## 4. Horas y responsables

Decisión: **Modifico**. Las reglas se expresan con consultas y condiciones de Python en los repositorios. SQLite conserva claves y restricciones por fila.

Archivo: `repositorio/registro_tiempo_repo.py`.

```python
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
```

Comprobación: Pruebas de altas y edición del total diario; comprobaciones de rol y pertenencia en empleado_repo.py y departamento_repo.py.

## 5. Fecha editada recibida como texto

Decisión: **Corrijo**. Una prueba detectó AttributeError al llamar isoformat sobre texto. La fecha se valida y convierte antes de consultar el acumulado; una edición rechazada conserva el registro guardado.

Archivo: `repositorio/registro_tiempo_repo.py`.

```python
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
```

Comprobación: test_editar_fecha_respeta_horas_del_dia_destino rechaza mover horas hacia un día completo y conserva el registro anterior. La conversión de fecha aparece en el fragmento precedente.

## 6. Transacción de contratación

Decisión: **Acepto y ajusto**. BEGIN agrupa comprobaciones y escrituras; commit confirma y rollback revierte. El ID se asigna al objeto después de confirmar.

Archivo: `repositorio/sistema_repo.py`.

```python
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
```

Comprobación: demo.py --caso rollback fuerza un proyecto inexistente: no quedan empleado ni asignación. conexion.py administra BEGIN, commit, rollback y cierre.

## 7. Gerencia mediante Empleado.rol

Decisión: **Acepto recomendación de IA**. La IA recomendó seguir C06 y representar la gerencia como rol. Se adapta la subclase Gerente del ES1 para cambiar la función sin duplicar al trabajador; se comprueban ID, rol y pertenencia al departamento.

Archivo: `dominio/empleado.py`.

```python
    @property
    def rol(self) -> str:
        """Lee el cargo actual sin cambiar la clase del empleado."""
        return self._rol

    @rol.setter
    def rol(self, valor: str):
        """Limita los roles a las opciones previstas."""
        if valor not in ('empleado', 'gerente'):
            raise DatoInvalidoError('El rol debe ser empleado o gerente.')
        self._rol = valor
```

Comprobación: test_gerente_es_rol_modificable comprueba conservación de clase e ID; las pruebas de responsables comprueban rol y departamento.

SQLite protege claves, unicidad y condiciones por fila. El acumulado diario y la coherencia del responsable requieren utilizar los repositorios de la aplicación. Los resultados generales están en evidencias/pruebas.txt y evidencias/revision_tecnica.txt.
