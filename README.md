# EcoTech Solutions · Evaluación Sumativa 3

Benjamin Olivares Mella · TI3021 · Programación Orientada a Objeto Seguro

Esta rama individual amplía EcoTech ES2 con inicio de sesión, consultas a Open-Meteo y Mi Indicador y respaldo local en SQLite. El menú vincula el clima con un proyecto y estima en USD o EUR el salario en CLP de un empleado asignado. Los cálculos se hacen localmente.

## Preparación en Windows

Abre PowerShell en la carpeta del proyecto. Usa Python 3.10 o posterior.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python.exe main.py
```

Copia `.env` una vez. La ruta de ejemplo es `datos/ecotech.db`. Para usar los datos anteriores pon una copia de la base ES2 en esa ruta antes de iniciar. Las nuevas tablas se crean sin borrar los datos de ES2. La primera vez se crea la cuenta local y se ingresa usando esa cuenta. Escribe la contraseña en una terminal interactiva.

## Recorrido en sala

1. Con red, crea un proyecto de prueba desde **3 Proyectos**. Usa **7 Contratar en proyecto** para crear y asignar un empleado ficticio, con salario de 800000 CLP, o asigna uno existente desde **5 Asignaciones**.
2. Abre **8 Servicios externos → 1 Clima del proyecto**. Selecciona el proyecto, consulta `Santiago` en `CL` y elige la ubicación. Lee la temperatura, el estado actual, la humedad y la hora UTC.
3. Abre **8 → 2 Estimar salario en otra moneda**. Selecciona el proyecto, el empleado y `USD`. Lee la tasa, la fecha del indicador y la estimación.
4. Cierra la aplicación y repite ambas consultas con la misma base, proyecto y entradas. La opción **8 → 3 Datos guardados** sigue mostrando una fila para el clima y otra para USD. Las respuestas exitosas actualizan el respaldo de esa consulta.
5. Desconecta la red y repite las consultas. El menú usa los datos guardados e indica su antigüedad y `obtenido_en` en UTC. Si nunca se consultó esa combinación, informa que falta el respaldo y permite continuar. La fecha del indicador y la fecha en que se guardó son datos distintos.

Para comprobar la base y simular fallos sin cambiar la conexión del computador:

```powershell
.venv\Scripts\python.exe -m unittest tests.test_es3 -v
.venv\Scripts\python.exe -m unittest discover -v
```

| Comprobación | Resultado esperado |
|---|---|
| Dos ejecuciones con las mismas consultas | Una fila por cada clave de consulta en `dato_externo`. |
| Corte de red después de una consulta exitosa | Aparece el Plan B con la hora original y la antigüedad. |
| Endpoint que responde 404 | Aparece `HTTP 404` y el menú sigue disponible. Se hace una solicitud. |
| Tabla de usuarios | `usuario.hash_clave` contiene un valor codificado de Argon2id con sal. |
| Defensa técnica | Se puede explicar el recorrido desde el menú hasta la API y SQLite. |

La suite usa bases temporales y respuestas simuladas. En el recorrido de sala, las consultas con red usan los proveedores reales.

## Archivos de ES3

- `api_cliente.py` controla TLS, espera, estados HTTP y reintentos.
- `servicios_externos.py` contiene la clase `Deserializador` y las reglas de clima y cotización.
- `repositorio/sistema_repo.py` guarda y recupera respuestas procesadas mediante SQL parametrizado.
- `acceso.py` administra la cuenta local con Argon2id.
- [Defensa técnica](REVISION_ES3.md) y [bitácora de IA](bitacora_ia.md).
