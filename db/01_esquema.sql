CREATE TABLE IF NOT EXISTS departamento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE CHECK(length(trim(nombre)) > 0),
    gerente_id INTEGER UNIQUE REFERENCES empleado(id) ON DELETE RESTRICT
);

-- Datos heredados: los datos personales no se duplican en tablas hijas.
CREATE TABLE IF NOT EXISTS empleado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL CHECK(length(trim(nombre)) > 0),
    direccion TEXT NOT NULL,
    telefono TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    fecha_inicio TEXT NOT NULL,
    salario REAL NOT NULL CHECK(salario > 0),
    departamento_id INTEGER REFERENCES departamento(id) ON DELETE RESTRICT,
    rol TEXT NOT NULL CHECK(rol IN ('empleado', 'gerente'))
);

CREATE TABLE IF NOT EXISTS proyecto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE CHECK(length(trim(nombre)) > 0),
    descripcion TEXT NOT NULL,
    fecha_inicio TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS empleado_proyecto (
    empleado_id INTEGER NOT NULL REFERENCES empleado(id) ON DELETE CASCADE,
    proyecto_id INTEGER NOT NULL REFERENCES proyecto(id) ON DELETE CASCADE,
    PRIMARY KEY(empleado_id, proyecto_id)
);

CREATE TABLE IF NOT EXISTS registro_tiempo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empleado_id INTEGER NOT NULL,
    proyecto_id INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    horas REAL NOT NULL CHECK(horas > 0 AND horas <= 24),
    descripcion TEXT NOT NULL,
    FOREIGN KEY(empleado_id, proyecto_id)
        REFERENCES empleado_proyecto(empleado_id, proyecto_id) ON DELETE RESTRICT
);

-- Retira los controles automáticos de versiones anteriores sin borrar datos.
-- Las reglas de responsables y horas se comprueban ahora en los repositorios.
DROP TRIGGER IF EXISTS gerente_al_insertar;
DROP TRIGGER IF EXISTS gerente_al_actualizar;
DROP TRIGGER IF EXISTS conservar_responsable;
DROP TRIGGER IF EXISTS horas_diarias_insertar;
DROP TRIGGER IF EXISTS horas_diarias_actualizar;
