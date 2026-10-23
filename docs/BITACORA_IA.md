# Bitácora de apoyo técnico con IA

Fecha: 20 de octubre de 2026. Herramienta: Codex. Entrega individual: Benjamin Olivares Mella.

Se solicitó apoyo para desarrollar la aplicación de EcoTech a partir del ES1, revisar consultas y relaciones, simplificar su lectura y documentar las comprobaciones. La IA intervino en la generación y corrección de código, documentación y pruebas.

| Fragmento | Decisión | Justificación |
| --- | --- | --- |
| Consultas parametrizadas | Modifico | Se sustituyó la construcción dinámica de la estructura SQL por sentencias literales completas. Los valores se envían por separado. La corrección elimina esa construcción; no se afirma que se haya reproducido una inyección en el borrador. |
| Rango de identificadores | Modifico | Se incorporó el máximo entero admitido por SQLite para impedir OverflowError y conservar el control del menú. |
| Organización del CRUD | Modifico | Las operaciones se concentran por entidad para seguir su recorrido completo. Se comparten conexión, validaciones y clases del dominio. |
| Horas y responsables | Modifico | Las reglas se expresan con consultas y condiciones de Python en los repositorios. SQLite conserva claves y restricciones por fila. |
| Fecha editada recibida como texto | Corrijo | Una prueba detectó AttributeError al llamar isoformat sobre texto. La fecha se valida y convierte antes de consultar el acumulado; una edición rechazada conserva el registro guardado. |
| Transacción de contratación | Acepto y ajusto | BEGIN agrupa comprobaciones y escrituras; commit confirma y rollback revierte. El ID se asigna al objeto después de confirmar. |
| Gerencia mediante Empleado.rol | Acepto recomendación de IA | La IA recomendó seguir C06 y representar la gerencia como rol. Se adapta la subclase Gerente del ES1 para cambiar la función sin duplicar al trabajador; se comprueban ID, rol y pertenencia al departamento. |

Los fragmentos finales y las comprobaciones se identifican en REVISION_TECNICA_IA.md. El registro de ejecución conserva 37 pruebas aprobadas con asistencia de IA.
