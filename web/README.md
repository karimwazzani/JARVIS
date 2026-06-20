# JARVIS Web

Dashboard web de JARVIS construido con Next.js 16 y React 19.

## Funciones actuales

- Estado general del sistema
- Modo activo de JARVIS
- Telemetria reciente
- Balance y graficos financieros
- Clima
- Calendario sincronizado
- Propuestas del motor de aprendizaje
- Compatible con el backend multiagente nuevo (`src/core/`, `src/agents/`, `src/core_files/`)

## Scripts

```bash
npm install
npm run dev
npm run lint
npm run build
```

## Variables de entorno utiles

- `DATABASE_URL`: conexion al Postgres usado por el dashboard
- `DASHBOARD_USER`: usuario para Basic Auth opcional
- `DASHBOARD_PASSWORD`: clave para Basic Auth opcional
- `NEXT_DIST_DIR`: override opcional del directorio de salida

## Deploy

- Vercel usa `../vercel.json`
- La build sale a `.next-prod`
- El acceso web puede protegerse con `web/src/proxy.ts`
- El dashboard hoy sigue leyendo el backend actual; una fase siguiente razonable es exponer trazas y estado por agente
