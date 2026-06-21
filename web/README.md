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

- `SUPABASE_URL`: URL del proyecto Supabase
- `SUPABASE_SERVICE_ROLE_KEY`: clave server-side para lecturas y acciones del dashboard
- `SUPABASE_ANON_KEY`: opcional, util para lecturas cliente o integraciones futuras
- `DASHBOARD_USER`: usuario para Basic Auth opcional
- `DASHBOARD_PASSWORD`: clave para Basic Auth opcional
- `NEXT_DIST_DIR`: override opcional del directorio de salida

## Deploy

- Vercel usa `../vercel.json`
- La build sale a `.next-prod`
- El acceso web puede protegerse con `web/src/proxy.ts`
- El dashboard hoy consulta Supabase server-side desde `web/src/app/actions.ts`
