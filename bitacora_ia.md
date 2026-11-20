# Bitácora de revisión técnica con IA · ES3

Codex asistió en la implementación y las pruebas. Esta bitácora documenta decisiones y comprobaciones sobre el código del proyecto. La revisión personal del estudiante se completa al repetir el recorrido y explicar una decisión con el resultado observado.

| Señal revisada | Decisión y motivo | Comprobación |
|---|---|---|
| F-strings o concatenación en SQL | Se usan sentencias fijas y marcadores `?` en el repositorio y en el acceso. La clave de consulta se construye en Python y se pasa como parámetro. SQLite se encarga de detectar la misma consulta con la clave primaria. | Se revisaron los `execute` de la rama. La suite de ES2 comprueba la construcción estática de las consultas del repositorio. |
| `verify=False` | Se conserva la validación TLS de Requests. Se distingue `SSLError` del fallo temporal de red, para que un certificado rechazado se vea como problema y termine la llamada. | Se revisó la llamada en `api_cliente.py`. |
| `except: pass` | Se capturan excepciones concretas. El cliente traduce los fallos a mensajes breves. El deserializador descarta una ubicación inválida si existen otras utilizables y avisa cuando se queda sin coincidencias válidas. | Pruebas de JSON inválido, HTTP 404, respuesta parcial y caída de red. |
| Llamadas HTTP sin `timeout` | Las APIs usan un único cliente con 4 s de conexión y 8 s de lectura por intento. Se permite un máximo de tres intentos para fallos temporales. | Se comprueban los argumentos de cada llamada y las esperas efectivas que se pedirían, incluidas las de HTTP 429. |
| Librerías inexistentes en PyPI | Se conservó `requests` y se añadió `argon2-cffi` para cumplir el requisito del AAI. Se comprobó el nombre de distribución y el módulo que se importa. | Instalación en un entorno virtual limpio, importación y `pip check`. [Requests en PyPI](https://pypi.org/project/requests/) y [argon2-cffi en PyPI](https://pypi.org/project/argon2-cffi/). |

## Decisiones que cambiaron respecto del borrador

- **Autenticación.** El borrador usaba PBKDF2. La pauta del AAI pide bcrypt o Argon2. Se eligió Argon2id porque `PasswordHasher` genera la sal y conserva en el hash codificado los parámetros requeridos para verificarlo.
- **Caída del proveedor.** Un mensaje y el retorno al menú eran insuficientes para el Plan B. Ahora se consulta SQLite después de un fallo temporal y se muestra la antigüedad original.
- **Persistencia.** El historial de textos podía duplicar entradas. La clave compuesta permite actualizar una sola fila por consulta. Se conservan los campos devueltos y se construye el texto al mostrarlo.
