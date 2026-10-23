# EcoTech Solutions ES2

Aplicación de consola que administra empleados, roles, departamentos, proyectos y horas. El informe ES1 se conserva como antecedente; la adaptación del modelo se explica en el informe ES2.

## Ejecutar en Windows

Necesitas Python 3.10 o posterior. No hay paquetes externos ni servidor de base de datos.

Abre una terminal en esta carpeta y ejecuta:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

Si `.env` ya existe, conserva su configuración. Si PowerShell impide activar el entorno, puedes ejecutar directamente `.venv\Scripts\python.exe main.py`; no necesitas cambiar políticas de seguridad. En CMD la activación es `.venv\Scripts\activate.bat`.

También puedes abrir `iniciar.cmd`: prepara `.env` solo si no existe y utiliza Python instalado. `main.py` inicializa las tablas automáticamente. La inicialización independiente es:

```powershell
python -c "from repositorio.conexion import BaseDatos; BaseDatos().inicializar()"
```

La configuración de ejemplo es `DB_NOMBRE=datos/ecotech.db`. La ruta se interpreta desde el proyecto. La variable DB_NOMBRE del entorno tiene prioridad. La base y `.env` son locales y no se entregan en el ZIP.

## Recorrido de uso

1. Crea un departamento, por ejemplo Contabilidad, y anota el ID.
2. Crea un proyecto con nombre, descripción y fecha AAAA-MM-DD.
3. Crea un empleado con dirección, teléfono, correo, fecha, salario positivo, rol `empleado` o `gerente` y un departamento opcional.
4. En Asignaciones, vincula su ID con el proyecto. También puedes usar Contratar en proyecto: guarda empleado y relación en una sola transacción.
5. Registra sus horas para ese proyecto. El acumulado por empleado y fecha no puede superar 24 horas.
6. Consulta, edita y elimina los registros mediante los submenús. Los IDs los asigna SQLite; usa los que muestra el programa.
7. Consulta Informes para ver nómina total y horas por proyecto. Es una colección mixta que llama a `exportar` sin condicionales por tipo.

En una edición, Enter conserva el dato. En departamento, `-` quita la asignación. Para dejar de ser responsable de un departamento, retira primero la responsabilidad en Asignaciones; después cambia el rol si corresponde.

## Pruebas y evidencias

```powershell
python -m unittest discover -v
python demo.py --caso sql
python demo.py --caso rollback
python demo.py --caso crud
```

Las pruebas y las demostraciones crean bases temporales propias dentro de `tests` y las eliminan al terminar. No usan los datos del menú. `--guardar` conserva la salida y su visor HTML en `evidencias`. Las capturas incluidas muestran esos resultados reales y se identifican como pruebas automatizadas con asistencia de IA.

## Organización

- `dominio`: entidades, propiedades, validaciones, excepciones e informes.
- `repositorio`: conexión compartida, cuatro repositorios con CRUD explícito y coordinación de relaciones.
- `db`: esquema con claves y restricciones.
- `main.py`: entradas y salidas por consola.
- `tests`: 37 pruebas automáticas.
- `demo.py`: demostración de SQL, rollback y operaciones del sistema.
- `evidencias`: resultados y capturas de ejecución.
- `docs`: revisión técnica de IA y modelo de clases.

Cada repositorio declara sentencias completas y contiene su CRUD explícito. Se utiliza la conexión compartida sin construir SQL. Los valores del usuario viajan como parámetros `?`. No hay f-strings, suma de cadenas ni formato `%` en las consultas.

Las relaciones con proyectos se guardan siempre mediante `SistemaEcoTech.vincular` y `desvincular`, ubicados en `repositorio/sistema_repo.py`. `actualizar` guarda los datos propios de una entidad, no relaciones implícitas. Las relaciones se guardan explícitamente mediante esas operaciones.

## Alcance y límites

Gerente es un rol del mismo Empleado; no existe una subclase Gerente. Los datos personales se heredan de Persona. Informe es abstracta y tiene dos implementaciones concretas. Los salarios son números reales del modelo académico; no se calcula sueldo líquido ni obligaciones laborales. No se incluyen autenticación, cifrado ni interfaz gráfica.

Los registros de horas bloquean el borrado del empleado, proyecto o asignación asociados. Los repositorios comprueban que los responsables tengan rol gerente y pertenezcan al departamento que dirigen. El dominio valida salarios, nombres, correo y fechas; SQLite respalda claves, unicidad y reglas por fila. El total diario se comprueba en RegistroTiempoRepositorio.

## Documentación y uso de IA

El trabajo se presenta individualmente por Benjamin Olivares Mella. Codex se utilizó como herramienta de apoyo en la generación y corrección de código, documentación y pruebas. Las solicitudes técnicas, los fragmentos y las decisiones se identifican en la sección 6 del informe y en `docs/BITACORA_IA.md`.

La documentación técnica incluye el informe Word/PDF, el modelo de clases y las fragmentos y comprobaciones que sustentan las decisiones de revisión.

## Relación con los ejemplos de clase

El menú pide los datos con formularios explícitos por entidad. El correo se valida con condiciones y operaciones de texto. Los repositorios convierten tuplas por posición como en C08. Se conservan el CRUD, las relaciones, las propiedades, la herencia, el polimorfismo, los parámetros y el rollback.

El CRUD explícito, los controles de horas y responsables en Python y las utilidades de pruebas se revisaron con apoyo de IA. Su motivo y las comprobaciones están en `docs/REVISION_TECNICA_IA.md`.

La responsabilidad de gerencia se administra mediante el rol del empleado y su relación con Departamento. SistemaEcoTech coordina su asignación y las operaciones que afectan a varias entidades.


