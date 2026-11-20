# EcoTech Solutions ES3

Aplicación de consola en Python con inicio de sesión y respaldo en SQLite. La opción **8 Servicios externos** consulta el clima de un proyecto y estima salarios en USD o EUR.

## Inicio en Windows

Con Python 3.10 o posterior, ejecuta en PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.venv\Scripts\python.exe main.py
```

En el primer inicio, crea la cuenta local. La base se guarda en `datos/ecotech.db`. Puedes colocar allí una copia de la base de ES2 antes de iniciar.

## Pruebas

```powershell
.venv\Scripts\python.exe -m unittest discover -v
```

Las pruebas usan bases temporales y simulan las respuestas de las APIs. [Bitácora de IA](bitacora_ia.md)
