# Defensa técnica · EcoTech ES3

## Qué ocurre al consultar

1. `main.py` verifica la cuenta local antes de mostrar el menú. La opción 8 pide un proyecto y la información necesaria para consultar.
2. `api_cliente.py` ejecuta la solicitud HTTPS con TLS verificado y aplica la política de reintentos.
3. `Deserializador` toma solo los campos que EcoTech usa. Valida tipos, rangos, fechas y la identidad del indicador antes de guardar. En geocodificación descarta las coincidencias incompletas y conserva las demás.
4. `SistemaEcoTech.guardar_dato_externo` guarda el resultado con parámetros y actualiza una única fila por proyecto, servicio y clave. El clima usa país y ciudad como clave. La cotización usa la moneda.
5. Si hay un fallo temporal de red, HTTP 5xx o HTTP 429 y el cliente ya terminó sus intentos, el menú busca el mismo respaldo. Muestra cuándo se obtuvo y su antigüedad. La lectura del respaldo conserva la fecha original.

## Decisiones que puedo señalar en el código

**Reintentos.** Hay como máximo tres solicitudes por llamada. El cliente espera 1 s y luego 2 s. Para HTTP 429 aplica también `Retry-After`, tanto en segundos como en fecha HTTP. Si el servidor pide una espera superior a 10 s, el cliente pasa al respaldo sin volver a consultar antes de tiempo. Los demás 4xx y una falla de TLS se informan de inmediato. Los tiempos de conexión y lectura de Requests se aplican a cada intento.

**Idempotencia.** Si siempre usáramos `INSERT`, ejecutar dos veces la misma consulta crearía dos filas. Usamos una clave primaria compuesta y `ON CONFLICT ... DO UPDATE`. Puedes consultar de nuevo y obtener el dato más reciente manteniendo una sola fila. Un fallo temporal conserva lo que quedó guardado.

**Autenticación.** Se usa Argon2id para la cuenta local. `PasswordHasher` genera la sal y la incorpora al hash codificado junto con los parámetros. `getpass` oculta la escritura. Se comprueba la contraseña antes de entrar al menú. Los permisos de lectura de SQLite dependen del sistema operativo. El límite de tres intentos corresponde a una ejecución. La cuenta de un borrador local previo con PBKDF2, si existe, pasa a Argon2id al ingresar correctamente.

**Privacidad.** Al proveedor de tipos de cambio se le solicita el indicador. La aplicación calcula localmente con el salario del empleado. El respaldo guarda la tasa, la moneda, la fecha y la fuente. La contraseña y el salario quedan fuera de la petición.

**Alcance del dato.** Open-Meteo da condiciones actuales estimadas por un modelo. El tipo de cambio se usa como referencia y la pantalla muestra la fecha de la observación. Un dato de respaldo puede estar desactualizado y aparece identificado como tal.

## Referencias técnicas

- [RFC 9110, Retry-After](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after).
- [Requests, documentación](https://requests.readthedocs.io/en/latest/user/advanced/#timeouts).
- [argon2-cffi, PasswordHasher](https://argon2-cffi.readthedocs.io/en/stable/api.html).
- [Open-Meteo, documentación](https://open-meteo.com/en/docs) y [Mi Indicador](https://mindicador.cl/).
