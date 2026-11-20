# Bitácora de IA · ES3

A solicitud del estudiante, Codex ejecutó pruebas automatizadas sobre los casos que la pauta indica para la evaluación en sala. Codex también apoyó la implementación.

| Qué se revisó | Decisión | Cómo se comprobó |
|---|---|---|
| F-strings o concatenación en SQL | Se mantuvieron sentencias fijas con parámetros `?` para enviar los valores por separado. | La suite comprueba que el repositorio use SQL estático. |
| `verify=False` | Se descartó desactivar la verificación TLS. | Una prueba simula un error TLS y comprueba que el cliente lo informa tras un solo intento. |
| `except: pass` | Se descartó silenciar errores. El cliente captura excepciones concretas y devuelve un mensaje breve. | Se simularon HTTP 404 y JSON inválido. |
| Solicitudes sin `timeout` | Se fijaron 4 s para conectar y 8 s para leer por intento. Se permiten hasta tres intentos ante fallos temporales. | Se comprobaron los tiempos configurados, las esperas de 1 y 2 s y el manejo de `Retry-After`. |
| Dependencias sin verificar | Se usaron [Requests](https://pypi.org/project/requests/) y [argon2-cffi](https://pypi.org/project/argon2-cffi/). | Ambas se instalaron en un entorno limpio y `pip check` pasó. |

Se eligió Argon2id para guardar el hash de la contraseña con sal. Ante una falla temporal, EcoTech usa el respaldo de SQLite si existe y muestra cuándo se obtuvo.
