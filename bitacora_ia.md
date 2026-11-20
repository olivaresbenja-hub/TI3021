# Bitácora de IA · ES3

Codex apoyó la implementación y las pruebas.

| Revisión | Decisión y comprobación |
|---|---|
| SQL construido con f-strings o concatenación | Sentencias fijas con parámetros `?`. Una clave primaria compuesta evita duplicar respaldos de la misma consulta. |
| `verify=False` | Requests verifica TLS. La prueba de certificado rechazado confirma que se informa el error sin reintentar. |
| `except: pass` | Se capturan errores concretos. Las pruebas muestran cómo se informan el HTTP 404 y el JSON inválido. |
| Solicitudes sin `timeout` | El cliente usa 4 s para conexión y 8 s para lectura por intento. Las pruebas revisan el máximo de tres intentos, las esperas de 1 y 2 s y el manejo de `Retry-After`. |
| Dependencias inexistentes | [Requests](https://pypi.org/project/requests/) y [argon2-cffi](https://pypi.org/project/argon2-cffi/) se instalaron en un entorno limpio. `pip check` pasó. |

Se eligió Argon2id para guardar el hash de la contraseña con sal. Ante una falla temporal de la API, EcoTech lee el último respaldo de SQLite y muestra su fecha original y su antigüedad.
