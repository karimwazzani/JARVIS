# JARVIS

Asistente personal orientado a automatizacion, monitoreo del hogar y gestion diaria, con backend en Python, bot de Telegram, herramientas de IA y dashboard web en Next.js.

## Que incluye

- Bot de Telegram para texto, voz, recordatorios, finanzas y modos del sistema.
- Motor de IA con herramientas locales para agenda, tareas, memoria y finanzas.
- Dashboard web para telemetria, calendario, clima, estado general y propuestas del sistema.
- Integracion con sensores locales, simulador IoT y soporte para camara Tapo.
- Worker persistente para Railway y frontend separado para Vercel.

## Stack

- Backend: Python 3.12, `python-telegram-bot`, SQLAlchemy, OpenAI, Flask
- Frontend: Next.js 16, React 19, TypeScript, Recharts
- Base de datos: SQLite local o Postgres por `DATABASE_URL` / `POSTGRES_URL`
- Deploy: Railway para el worker Python, Vercel para el dashboard

## Estructura

- `src/`: backend principal, bot, base de datos, integraciones y logica de IA
- `src/core/`: runtime multiagente, guardian, orquestador y memoria
- `src/agents/`: especialistas enrutable por dominio
- `src/core_files/`: identidad, reglas y memoria base por agente
- `api/`: webhook liviano para entornos serverless
- `web/`: dashboard en Next.js
- `scratch/`: utilidades y scripts de apoyo

## Arquitectura multiagente

JARVIS ahora empieza a migrar de un agente unico a un sistema jerarquico inspirado en un "manager + especialistas":

- `Jarvis Orchestrator`: recibe el pedido, decide la ruta y arma la respuesta final.
- `Memory Keeper`: inyecta memoria persistente y preferencias del usuario.
- `Guardian`: detecta acciones sensibles y obliga a pasar por aprobacion humana.
- `15 agentes especialistas`: contenido, produccion, publishing, growth, coder, QA, devops, research, CRM, finance, inbox, agenda y control.

La primera integracion real ya quedo conectada al flujo del bot:

- `text_handler` y `voice_handler` pasan por `src/core/orchestrator.py`
- cada turno se clasifica por keywords
- el especialista activo recibe sus `core files`
- la ejecucion sigue usando el motor actual de `src/ai_agent.py` para no romper herramientas existentes

Resumen tecnico del MVP:

```text
Telegram -> bot_handlers -> JarvisOrchestrator
                         -> MemoryKeeper
                         -> Specialist Agent
                         -> legacy ai_agent toolchain
                         -> Guardian note si aplica
```

## Seguridad actual

- El bot y el webhook pueden limitarse a chats autorizados con `AUTHORIZED_CHAT_IDS`.
- El dashboard puede protegerse con `DASHBOARD_USER` y `DASHBOARD_PASSWORD`.
- `.env`, bases locales, claves privadas y artefactos locales quedaron fuera del tracking.

## Variables de entorno

Base:

- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`

Opcionales recomendadas:

- `AUTHORIZED_CHAT_IDS`
- `DASHBOARD_USER`
- `DASHBOARD_PASSWORD`
- `DATABASE_URL` o `POSTGRES_URL`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ANON_KEY`
- `TAPO_USER`
- `TAPO_PASSWORD`
- `TAPO_IP`

Google Calendar:

- `credentials.json`
- `token.pickle`

## Desarrollo local

Backend:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

Frontend:

```bash
cd web
npm install
npm run dev
```

Checks utiles:

```bash
cd web
npm run lint
npm run build
```

## Deploy

### Railway

- Usa `Procfile` con `worker: python src/main.py`
- El `Dockerfile` ya esta preparado para correr el worker persistente
- Defini las variables del bot, OpenAI y base de datos en Railway

### Vercel

- El proyecto debe apuntar a `web/` como Root Directory
- La salida de build se genera en `.next-prod`
- Defini `DASHBOARD_USER` y `DASHBOARD_PASSWORD` si queres proteger el panel
- El dashboard puede trabajar directo con Supabase usando `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`

## Estado actual

Hoy el proyecto ya tiene:

- lint del frontend en verde
- build del frontend en verde
- sintaxis Python validada
- una capa inicial de hardening aplicada

Quedan como siguientes pasos razonables:

- reemplazar el ruteo por keywords por clasificacion LLM con trazabilidad
- separar tools por dominio (`finance`, `calendar`, `content`, `ops`) en modulos propios
- persistir memoria y trazas por agente en tablas dedicadas
- migraciones reales de base de datos
- unificar mejor polling y webhook para reducir duplicacion
- autenticacion mas fuerte en el dashboard
- mejor documentacion de sensores y despliegue
