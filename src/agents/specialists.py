from __future__ import annotations

from src.agents.base import BaseAgent


AGENTS: list[BaseAgent] = [
    BaseAgent(
        agent_id="jarvis_orchestrator",
        label="Jarvis Orchestrator",
        description="Recibe la solicitud, la clasifica y coordina la salida final.",
        keywords=("jarvis", "orquesta", "coordina", "sistema"),
    ),
    BaseAgent(
        agent_id="memory_keeper",
        label="Memory Keeper",
        description="Administra memoria persistente, preferencias y contexto del usuario.",
        keywords=("recorda", "recuerda", "acordate", "memoria", "preferencia", "te dije"),
    ),
    BaseAgent(
        agent_id="content_strategist",
        label="Content Strategist",
        description="Diseña angulos, hooks, calendario y estrategias de contenido.",
        keywords=("instagram", "reel", "contenido", "hook", "caption", "post", "viral", "marketing"),
    ),
    BaseAgent(
        agent_id="editor_producer",
        label="Editor Producer",
        description="Piensa edicion, secuencias, tomas, miniaturas y entregables audiovisuales.",
        keywords=("editar", "edicion", "thumbnail", "miniatura", "video", "corte", "b-roll"),
    ),
    BaseAgent(
        agent_id="publisher",
        label="Publisher",
        description="Publica, programa y adapta contenido a cada plataforma.",
        keywords=("publica", "publicar", "programa", "schedule", "subi", "subir"),
    ),
    BaseAgent(
        agent_id="growth_analytics",
        label="Growth Analytics",
        description="Mide performance, encuentra patrones y propone iteraciones.",
        keywords=("metricas", "analytics", "alcance", "engagement", "conversion", "growth"),
    ),
    BaseAgent(
        agent_id="coder",
        label="Coder",
        description="Desarrolla features, arregla bugs y propone arquitectura tecnica.",
        keywords=("codigo", "code", "bug", "feature", "backend", "frontend", "api", "python", "next", "refactor"),
    ),
    BaseAgent(
        agent_id="qa_tester",
        label="QA Tester",
        description="Valida comportamiento, casos borde y pruebas automatizadas.",
        keywords=("test", "qa", "prueba", "valida", "regresion", "caso borde"),
    ),
    BaseAgent(
        agent_id="devops_deploy",
        label="DevOps Deploy",
        description="Se ocupa de deploy, pipelines, infraestructura y observabilidad.",
        keywords=("deploy", "vercel", "railway", "render", "docker", "ci", "build", "env", "produccion"),
    ),
    BaseAgent(
        agent_id="research",
        label="Research",
        description="Hace investigacion de mercado, competencia y fuentes.",
        keywords=("investiga", "analiza", "competencia", "mercado", "tendencia", "fuente"),
    ),
    BaseAgent(
        agent_id="customer_crm",
        label="Customer CRM",
        description="Gestiona soporte, mensajes, leads y seguimiento comercial.",
        keywords=("cliente", "crm", "lead", "seguimiento", "soporte", "whatsapp"),
    ),
    BaseAgent(
        agent_id="finance_ops",
        label="Finance Ops",
        description="Ordena gastos, ingresos, facturacion y salud operativa.",
        keywords=("gasto", "ingreso", "factura", "mrr", "finanzas", "balance"),
    ),
    BaseAgent(
        agent_id="inbox_email",
        label="Inbox Email",
        description="Triagea inbox y redacta respuestas claras.",
        keywords=("mail", "email", "correo", "inbox", "responde"),
    ),
    BaseAgent(
        agent_id="calendar_scheduler",
        label="Calendar Scheduler",
        description="Ordena agenda, reuniones, bloques y recordatorios.",
        keywords=("agenda", "calendario", "reunion", "recordatorio", "turno", "schedule"),
    ),
    BaseAgent(
        agent_id="guardian",
        label="Guardian",
        description="Controla permisos, aprobaciones y acciones sensibles.",
        keywords=("seguridad", "permiso", "guardian", "aprobar", "confirmar"),
    ),
]


def get_agent_registry() -> dict[str, BaseAgent]:
    return {agent.agent_id: agent for agent in AGENTS}

