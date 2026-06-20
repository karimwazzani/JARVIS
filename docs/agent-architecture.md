# JARVIS Multi-Agent Blueprint

## Objetivo

Llevar JARVIS desde un asistente monolitico a un sistema de agentes especializados, con memoria persistente, permisos claros y capacidad de escalar por dominios.

## Estado actual

Hoy el proyecto ya tiene un MVP operativo:

1. `JarvisOrchestrator` enruta cada turno.
2. `MemoryKeeper` arma un snapshot desde `Memoria` y `PreferenciaUsuario`.
3. `Guardian` marca acciones sensibles.
4. Los especialistas cargan `identity.md`, `rules.md` y `memory.md`.
5. La respuesta final sigue ejecutandose sobre `src/ai_agent.py` para mantener compatibilidad.

## Los 15 agentes

1. Jarvis Orchestrator
2. Memory Keeper
3. Content Strategist
4. Editor Producer
5. Publisher
6. Growth Analytics
7. Coder
8. QA Tester
9. DevOps Deploy
10. Research
11. Customer CRM
12. Finance Ops
13. Inbox Email
14. Calendar Scheduler
15. Guardian

## Por que esta arquitectura sirve

- evita seguir agrandando `ai_agent.py` como punto unico de fallo
- permite permisos y aprobaciones por dominio
- hace mas facil desplegar agentes como workers o servicios separados despues
- deja un camino claro para sumar trazabilidad, metricas y testing por agente

## Siguiente fase recomendada

### Fase 1

- modularizar herramientas del agente legacy
- agregar tabla `agent_runs` y `agent_memories`
- registrar `route`, latencia y tool calls

### Fase 2

- clasificador LLM para ruteo
- colas por especialidad
- aprobaciones activas para deploys, publicaciones y acciones destructivas

### Fase 3

- panel web de agentes
- observabilidad por route
- ejecucion semiautonoma con workflows repetibles
