# Revisión crítica de producto — HelloChusquis

**Estado:** revisión técnica posterior a auditoría y recorridos de usuario locales.  
**Criterio:** fiabilidad operativa, aislamiento entre usuarios, seguridad y coherencia de producto.

> El proyecto tiene una ambición fuerte —un agente con terminal, web, API y proveedores múltiples—, pero antes de esta intervención confundía amplitud de catálogo con madurez. Una lista de integraciones no equivale a un producto fiable si el primer arranque puede bloquear un servidor, si la interfaz web queda abierta por defecto o si dos usuarios pueden compartir contexto.

| Área | Hallazgo crítico | Impacto | Decisión de producto |
|---|---|---:|---|
| Arranque | La API y la web lanzaban un asistente interactivo durante la importación si faltaba configuración. | Alto | Convertir el fallo en estado de preparación recuperable, manteniendo vivo el proceso. |
| Configuración | El agente recibía una configuración pero volvía a buscarla en disco; además, un proveedor local sin clave podía ser descartado. | Alto | Usar la configuración recibida y aceptar configuraciones locales válidas. |
| Seguridad web | La web exponía acciones potentes con autenticación desactivada por defecto. | Crítico | Autenticación obligatoria por defecto, con excepción explícita solo para desarrollo aislado. |
| Concurrencia | La web reemplazaba temporalmente el despachador global de herramientas para registrar llamadas. | Alto | Sustituirlo por callbacks propios de cada solicitud. |
| Privacidad | El servidor reutilizaba un único historial de conversación para todos los clientes HTTP. | Crítico | Introducir sesiones de agente aisladas y acotadas con LRU. |
| Operación | Faltaban rutas claras de recuperación tras ejecutar `setup`; los comandos de inspección podían abrir un asistente. | Medio | Añadir recarga en vivo y hacer no interactivos los comandos de diagnóstico. |
| Coherencia | La versión anunciada, la CLI y la documentación no compartían una fuente única de verdad. | Medio | Centralizar la versión y corregir documentación/ayuda. |
| Calidad | La cobertura inicial era del 14 % y no validaba web, API ni proveedor real. | Alto | Añadir regresiones y recorridos HTTP autenticados con proveedor local simulado. |

La conclusión es deliberadamente dura: **no era defendible presentar el sistema como un agente de nivel producción o comparable a un agente maduro mientras fallaban aislamiento, arranque no interactivo y autenticación por defecto**. Esas carencias ya están abordadas en esta rama; las funcionalidades restantes de esta revisión son la recuperación explícita en caliente y la coherencia verificable de versión.

## Mejoras que se implementan a continuación

| Funcionalidad | Resultado esperado | Verificación |
|---|---|---|
| Recarga en vivo del runtime | Tras ejecutar la configuración, un operador autorizado puede reconstruir agentes sin reiniciar el proceso. | Ruta protegida y prueba de éxito/error. |
| Observabilidad de sesiones | El estado informa de sesiones activas en memoria sin filtrar historiales. | Campo de estado y prueba de sesiones aisladas. |
| Fuente única de versión | CLI, API y web devuelven la misma versión publicada. | Pruebas unitarias y comprobación de comandos. |
| Contrato de uso actualizado | La ayuda y la guía reflejan puerto real, autenticación por defecto y recuperación. | Revisión de README y salida `--help`. |

## Límites que siguen siendo reales

El límite de sesiones protege la memoria, pero no reemplaza autenticación multiusuario, aislamiento de procesos por cliente, auditoría de permisos ni una cola de trabajos. Las más de cien integraciones declaradas requieren pruebas contractuales independientes antes de prometer soporte de producción. Un modelo de lenguaje tampoco vuelve seguro un comando: la política de herramientas necesita pruebas adversariales continuas y controles de aprobación para acciones destructivas o externas.

## Actualización de madurez — segunda iteración

La segunda iteración transforma uno de los límites más graves de la primera revisión —la ejecución autónoma de acciones con efectos externos— en un flujo verificable de **propuesta, aprobación explícita y ejecución única**. En las superficies HTTP, las herramientas de shell y código, la mutación de archivos, los envíos del navegador, las llamadas MCP y las acciones externas con verbos mutables dejan de ejecutarse de inmediato. El agente crea una solicitud local a la sesión, caducable y con un identificador opaco; el usuario autenticado debe aprobarla o rechazarla.

| Capacidad desarrollada | Garantía implementada | Evidencia de validación |
|---|---|---|
| Aprobaciones humanas | Las acciones de alto impacto requieren decisión explícita en API y web. | Pruebas unitarias de clasificación, denegación y aprobación. |
| Protección contra repetición | La aprobación pasa a estado de ejecución antes de despachar la herramienta; un segundo intento falla. | Recorrido HTTP: aprobación única seguida de respuesta `409` al repetirla. |
| Aislamiento de aprobación | Las solicitudes pertenecen al agente de una única sesión HTTP. | Recorrido adversarial: una segunda sesión ve una lista vacía y recibe `404` al intentar decidir. |
| Caducidad y límite | Las solicitudes pendientes expiran a los cinco minutos y la cola está acotada. | Pruebas con reloj controlado y deduplicación de solicitudes equivalentes. |
| Secreto mínimo | La vista pública de la aprobación redacta claves, tokens, cookies, contraseñas y secretos. | Prueba de regresión de redacción recursiva. |
| Streaming estructurado | El agente emite un evento SSE de aprobación con el identificador y motivo exactos. | Recorrido con proveedor local simulado y tarjeta de confirmación en el cliente. |
| Compatibilidad HTTP | Una aprobación de archivo evita que un servidor se bloquee solicitando confirmación por terminal. | Recorrido de escritura controlada: inexistente antes de aprobar y creada después. |
| Diagnóstico contractual | `hellochusquis doctor --contracts` importa y comprueba el punto de entrada de las 48 integraciones expuestas por el agente, sin red ni credenciales. | Ejecución local: 48/48 contratos estructurales válidos. |

> **Veredicto sin maquillaje:** el proyecto ha dado un salto real de "agente que ejecuta" a "agente que pide autorización antes de cambiar cosas". Eso era imprescindible. Sin embargo, esta mejora no convierte por sí sola el producto en equivalente a Hermes Agent ni autoriza a afirmar tal equivalencia.

## Límites pendientes para una paridad seria con un agente de primer nivel

| Brecha restante | Por qué sigue importando | Siguiente inversión necesaria |
|---|---|---|
| Aislamiento de procesos | Las sesiones separan historial y aprobaciones, pero comparten proceso, red y almacenamiento local. | Ejecutores efímeros aislados por tarea con límites de CPU, memoria, archivos y red. |
| Identidad multiusuario | Un único token de API identifica al despliegue, no a personas o roles separados. | Autenticación de usuarios, roles, propietarios de sesión y autorización por herramienta. |
| Auditoría durable | Las aprobaciones viven en memoria y se pierden al reiniciar. | Registro persistente, inmutable y consultable de decisiones, argumentos redactados y resultados. |
| Integraciones reales | La verificación contractual garantiza importación y `run`, no credenciales válidas ni comportamiento de cada proveedor. | Suites de contrato con entornos sandbox/mocks por proveedor y pruebas de versión de API. |
| Política semántica | La clasificación por herramienta y verbo es conservadora, pero no entiende todos los efectos de negocio. | Esquemas de riesgo por acción, límites monetarios y aprobaciones escalonadas. |
| Recuperación de ejecución | Tras aprobar, la acción se ejecuta y se muestra su resultado; el modelo no reanuda automáticamente el plan con ese resultado. | Orquestación de tareas con estados durables, reanudación y compensación. |

La validación al cierre de esta iteración incluye **89 pruebas unitarias**, compilación completa, análisis estático de los archivos modificados, revisión de seguridad de alta severidad, pruebas HTTP con proveedor local simulado, prueba de repetición y prueba adversarial de sesión cruzada. Esta evidencia respalda las capacidades descritas; no debe extrapolarse a una garantía sobre APIs externas no probadas.

## Prioridad recomendada

La ruta racional hacia un agente realmente robusto no es añadir más logos de integraciones. Es construir, en este orden: **identidad multiusuario y roles**, **auditoría persistente de decisiones**, **ejecución aislada por tarea** y **pruebas de contrato por proveedor**. Todo lo demás es cosmética hasta que esas cuatro capas estén presentes.
