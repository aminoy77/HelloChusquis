# Revisión de experiencia de usuario

**Fecha:** 20 de agosto de 2026  
**Alcance:** Primera ejecución de CLI sin configuración previa, diagnóstico offline y recuperación hacia la configuración inicial.

## Recorrido realizado

Se ejecutaron los flujos que seguiría una persona que instala la herramienta y busca comprobar su estado antes de conectar un proveedor: `hellochusquis --help`, `hellochusquis doctor --contracts`, `hellochusquis doctor`, `hellochusquis config --show` y el comando intuitivo `hellochusquis status`.

El recorrido base es sólido. La ayuda enumera las acciones principales, el diagnóstico de contratos funciona sin red y las rutas sin configuración responden con una instrucción concreta para ejecutar `hellochusquis setup`. Esto evita que una instalación incompleta falle con rastros internos o asistencias ambiguas.

## Fricciones verificadas

| Prioridad | Hallazgo observado | Impacto para la persona usuaria | Mejora comprometida |
|---|---|---|---|
| Alta | `hellochusquis status` no existe y responde como comando desconocido. | El comando más natural para comprobar preparación falla, aunque `doctor` ofrece parte de esa información. | Añadir `status` como resumen no interactivo de configuración, preparación y contratos opcionales. |
| Alta | La API CLI se expone por defecto en `0.0.0.0`. | Una persona puede publicar una API autenticada en su red por accidente durante la primera ejecución. | Cambiar el valor predeterminado a `127.0.0.1`; mantener `--host 0.0.0.0` como elección explícita. |
| Media | El diagnóstico de configuración y los contratos son comandos separados. | Es necesario recordar qué comprobación usar según el tipo de problema. | El nuevo estado presentará una vista rápida de preparación local y ofrecerá una opción para incluir contratos sin conexión. |

## Criterio de aceptación

Las mejoras deben mantener el diagnóstico existente, no revelar secretos ni rutas locales, y conservar la posibilidad explícita de exponer la API cuando el operador lo necesite. Deben incluir pruebas de regresión de CLI y la batería integral del proyecto.
