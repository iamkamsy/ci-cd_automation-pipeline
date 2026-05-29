# Task Manager - Frontend

React + TypeScript frontend for the Task Manager app, built with Vite and Tailwind CSS.

## Prerequisites

- Node.js 18+
- Backend running on `http://localhost:5000` (see `../backend/`)

## Development

```bash
npm install
npm run dev
```

The dev server starts at `http://localhost:5173`. All `/api/*` requests are proxied to `http://localhost:5000` via the Vite proxy configured in `vite.config.ts`.

## Build

```bash
npm run build
```

Output goes to `dist/`. Serve these static files behind nginx or any static host in production.

## Lint

```bash
npm run lint
```

## Vite Proxy

In development, `vite.config.ts` forwards any request matching `/api` to `http://localhost:5000`, so the frontend and backend run on separate ports without CORS issues. In production, nginx handles the same forwarding.

## Source Layout

```
src/
  api/          # task fetch helpers and SessionExpiredError
  components/   # shadcn/ui components (Button, Input, Label, Card, ...)
  context/      # AuthContext - user state, login/logout/signup
  pages/        # AuthPage.tsx, TasksPage.tsx
  types/        # task.ts type definition
  App.tsx       # root component - renders AuthPage or TasksPage based on auth state
  main.tsx      # React entry point
  index.css     # Tailwind CSS import
```
