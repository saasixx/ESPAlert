# ESPAlert Web

Frontend de ESPAlert construido con Next.js App Router, Tailwind y MapLibre.

> 🇪🇸 **Español** | 🇬🇧 [English](README.en.md)

## Scripts

```bash
npm run dev      # Inicia el servidor de desarrollo con hot reload
npm run build    # Compila para producción
npm run start    # Inicia el servidor de producción
npm run lint     # Ejecuta ESLint
```

## Desarrollo local

1. Desde la raíz del monorepo instala dependencias:

```bash
npm install
```

2. Levanta el frontend:

```bash
npm run dev --workspace=web
```

3. Abre `http://localhost:3000`.

## Configuración

Este paquete consume la API del backend de ESPAlert. Revisa la configuración
central en el README raíz para entorno Docker y variables de entorno.

## Estructura principal

- `src/app/` — rutas y layout (App Router)
- `src/components/map/` — mapa, popup y detalle de alertas
- `src/hooks/` — hooks de WebSocket, filtros y media query
- `src/lib/` — cliente API y utilidades
