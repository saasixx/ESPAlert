# ESPAlert Web

Frontend of ESPAlert built with Next.js App Router, Tailwind, and MapLibre.

> 🇪🇸 [Español](README.md) | 🇬🇧 **English**

## Scripts

```bash
npm run dev      # Start development server with hot reload
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
npm run test     # Run unit tests (Vitest)
```

## Local Development

1. From the monorepo root, install dependencies:

```bash
npm install
```

2. Start the frontend:

```bash
npm run dev --workspace=web
```

3. Open `http://localhost:3000`.

## Configuration

This package consumes the ESPAlert backend API. Review the main README for
Docker environment setup and environment variables.

## Main Structure

- `src/app/` — Routes and layout (App Router)
- `src/components/map/` — Map, popup, and alert detail components
- `src/hooks/` — WebSocket, filter, and media query hooks
- `src/lib/` — API client and utilities
