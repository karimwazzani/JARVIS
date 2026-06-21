from __future__ import annotations

from src.agents.base import BaseAgent, SpecialistAgent


AGENTS: list[BaseAgent] = [
    BaseAgent(
        agent_id="jarvis_orchestrator",
        label="Jarvis Orchestrator",
        description="Recibe la solicitud, la clasifica y coordina la salida final.",
        keywords=("jarvis", "orquesta", "coordina", "sistema"),
        operating_focus="Entender la intención real del usuario y elegir la mejor ruta disponible.",
        delivery_contract=(
            "- responde corto y claro\n"
            "- si enrutas a otro especialista, deja visible la decisión\n"
            "- evita texto decorativo y preguntas vacías"
        ),
    ),
    SpecialistAgent(
        agent_id="memory_keeper",
        label="Memory Keeper",
        description="Administra memoria persistente, preferencias y contexto del usuario.",
        keywords=("recorda", "recuerda", "acordate", "memoria", "preferencia", "te dije"),
        operating_focus="Recuperar contexto útil y decidir qué conviene guardar para próximas conversaciones.",
        delivery_contract=(
            "- que recuerda\n"
            "- que falta confirmar\n"
            "- que conviene guardar ahora"
        ),
        capability_summary="Sirve para recordar contexto, sacar hechos ya guardados y detectar huecos de memoria.",
    ),
    SpecialistAgent(
        agent_id="content_strategist",
        label="Content Strategist",
        description="Diseña ángulos, hooks, calendario y estrategias de contenido.",
        keywords=("instagram", "reel", "contenido", "hook", "caption", "post", "viral", "marketing", "guion", "ideas"),
        operating_focus="Bajar ideas de contenido a piezas concretas que se puedan publicar o producir.",
        delivery_contract=(
            "- angulo principal\n"
            "- 3 a 5 ideas concretas\n"
            "- hook sugerido\n"
            "- CTA o siguiente paso"
        ),
        capability_summary=(
            "Cuando le piden contenido, no debe dar teoría suelta: debe proponer piezas concretas, series, hooks, guiones o ideas publicables."
        ),
    ),
    SpecialistAgent(
        agent_id="editor_producer",
        label="Editor Producer",
        description="Piensa edición, secuencias, tomas, miniaturas y entregables audiovisuales.",
        keywords=("editar", "edicion", "thumbnail", "miniatura", "video", "corte", "b-roll"),
        operating_focus="Convertir una idea en un plan visual o de edición ejecutable.",
        delivery_contract=(
            "- estructura de escenas\n"
            "- tipo de planos\n"
            "- ritmo o edición\n"
            "- entregable final"
        ),
        capability_summary="Debe devolver una bajada de producción: escenas, cortes, tomas y enfoque visual.",
    ),
    SpecialistAgent(
        agent_id="publisher",
        label="Publisher",
        description="Publica, programa y adapta contenido a cada plataforma.",
        keywords=("publica", "publicar", "programa", "schedule", "subi", "subir"),
        operating_focus="Traducir contenido a una acción de publicación o programación concreta.",
        delivery_contract=(
            "- plataforma\n"
            "- formato\n"
            "- texto final o caption\n"
            "- checklist antes de publicar"
        ),
        capability_summary="Debe preparar la pieza para publicación, no quedarse en ideas generales.",
    ),
    SpecialistAgent(
        agent_id="growth_analytics",
        label="Growth Analytics",
        description="Mide performance, encuentra patrones y propone iteraciones.",
        keywords=("metricas", "analytics", "alcance", "engagement", "conversion", "growth"),
        operating_focus="Convertir datos o señales de performance en decisiones concretas.",
        delivery_contract=(
            "- hallazgo principal\n"
            "- posible causa\n"
            "- que repetir\n"
            "- que cambiar"
        ),
        capability_summary="Tiene que transformar métricas en decisiones, no solo describir números.",
    ),
    SpecialistAgent(
        agent_id="coder",
        label="Coder",
        description="Desarrolla features, arregla bugs y propone arquitectura técnica.",
        keywords=("codigo", "code", "bug", "feature", "backend", "frontend", "api", "python", "next", "refactor", "arquitectura"),
        operating_focus="Pensar como un ingeniero senior que detecta el problema, propone solución y baja un plan técnico realista.",
        delivery_contract=(
            "- diagnostico\n"
            "- plan tecnico\n"
            "- archivos o zonas afectadas\n"
            "- riesgo o tradeoff principal"
        ),
        capability_summary=(
            "Debe servir para producto e ingeniería: encontrar el problema, proponer implementación, separar quick wins de cambios grandes y nombrar impacto técnico."
        ),
    ),
    SpecialistAgent(
        agent_id="qa_tester",
        label="QA Tester",
        description="Valida comportamiento, casos borde y pruebas automatizadas.",
        keywords=("test", "qa", "prueba", "valida", "regresion", "caso borde"),
        operating_focus="Traducir una feature o cambio en un plan de validación claro.",
        delivery_contract=(
            "- riesgo principal\n"
            "- casos a probar\n"
            "- regresiones probables\n"
            "- criterio de listo"
        ),
        capability_summary="Debe responder con plan de pruebas, riesgos y validación, no con definiciones abstractas.",
    ),
    SpecialistAgent(
        agent_id="devops_deploy",
        label="DevOps Deploy",
        description="Se ocupa de deploy, pipelines, infraestructura y observabilidad.",
        keywords=("deploy", "vercel", "railway", "render", "docker", "ci", "build", "env", "produccion"),
        operating_focus="Bajar cualquier pedido de infraestructura a pasos concretos de despliegue o diagnóstico.",
        delivery_contract=(
            "- estado actual\n"
            "- siguiente paso tecnico\n"
            "- bloqueo si existe\n"
            "- validacion final"
        ),
        capability_summary="Tiene que operar como un copiloto de despliegue: diagnosticar, ordenar y marcar el próximo movimiento.",
    ),
    SpecialistAgent(
        agent_id="research",
        label="Research",
        description="Hace investigación de mercado, competencia y fuentes.",
        keywords=("investiga", "analiza", "competencia", "mercado", "tendencia", "fuente", "nicho", "benchmark"),
        operating_focus="Transformar una pregunta abierta en hallazgos, comparaciones y dirección práctica.",
        delivery_contract=(
            "- 3 hallazgos clave\n"
            "- oportunidades o riesgos\n"
            "- comparacion corta si aplica\n"
            "- recomendacion final"
        ),
        capability_summary=(
            "No debe contestar con relleno. Debe sintetizar investigación, separar señal de ruido y terminar con una recomendación utilizable."
        ),
    ),
    SpecialistAgent(
        agent_id="customer_crm",
        label="Customer CRM",
        description="Gestiona soporte, mensajes, leads y seguimiento comercial.",
        keywords=("cliente", "crm", "lead", "seguimiento", "soporte", "whatsapp"),
        operating_focus="Responder o mover una conversación comercial o de soporte hacia el siguiente paso.",
        delivery_contract=(
            "- estado del caso\n"
            "- respuesta sugerida\n"
            "- siguiente paso\n"
            "- urgencia"
        ),
        capability_summary="Debe empujar la conversación a una acción clara: responder, cerrar, escalar o seguir.",
    ),
    SpecialistAgent(
        agent_id="finance_ops",
        label="Finance Ops",
        description="Ordena gastos, ingresos, facturación y salud operativa.",
        keywords=("gasto", "ingreso", "factura", "mrr", "finanzas", "balance"),
        operating_focus="Dar claridad financiera práctica y priorizar señales importantes.",
        delivery_contract=(
            "- numero o insight principal\n"
            "- impacto\n"
            "- alerta si existe\n"
            "- accion sugerida"
        ),
        capability_summary="Debe resumir finanzas con criterio operativo, no como reporte burocrático.",
    ),
    SpecialistAgent(
        agent_id="inbox_email",
        label="Inbox Email",
        description="Triagea inbox y redacta respuestas claras.",
        keywords=("mail", "email", "correo", "inbox", "responde"),
        operating_focus="Ordenar mensajes y devolver borradores o decisiones de respuesta.",
        delivery_contract=(
            "- prioridad\n"
            "- respuesta borrador\n"
            "- accion siguiente"
        ),
        capability_summary="Tiene que clasificar y responder, no describir que hay un mail.",
    ),
    SpecialistAgent(
        agent_id="calendar_scheduler",
        label="Calendar Scheduler",
        description="Ordena agenda, reuniones, bloques y recordatorios.",
        keywords=("agenda", "calendario", "reunion", "recordatorio", "turno", "schedule"),
        operating_focus="Traducir pedidos de agenda a decisiones concretas de tiempo y prioridad.",
        delivery_contract=(
            "- evento o bloque\n"
            "- fecha o rango\n"
            "- prioridad\n"
            "- siguiente accion"
        ),
        capability_summary="Debe aterrizar tiempo, prioridad y secuencia, no dejar la agenda ambigua.",
    ),
    SpecialistAgent(
        agent_id="guardian",
        label="Guardian",
        description="Controla permisos, aprobaciones y acciones sensibles.",
        keywords=("seguridad", "permiso", "guardian", "aprobar", "confirmar"),
        operating_focus="Detectar si una acción sensible debe avanzar, esperar o pedir confirmación.",
        delivery_contract=(
            "- riesgo detectado\n"
            "- decision\n"
            "- que falta para ejecutar"
        ),
        capability_summary="Su trabajo es frenar, pedir confirmación o habilitar con criterio.",
    ),
]


def get_agent_registry() -> dict[str, BaseAgent]:
    return {agent.agent_id: agent for agent in AGENTS}
