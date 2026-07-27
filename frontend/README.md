# PersonalVoice Reader — frontend

Next.js 15 (App Router) + TypeScript + Tailwind CSS + React Query +
Zustand. Wired to the real backend — no more fixture data (`src/data/mock.ts`
is now unused, kept only for the `formatDuration` helper).

## Run locally

```bash
cd frontend
npm install
cp .env.local.example .env.local   # points at http://localhost:8000
npm run dev
```

Open http://localhost:3000. Flow: `/upload` → `/voices/new` (train a
voice) → open a book → choose the voice → generate a chapter → play.

Requires normal internet access on first build so `next/font` can fetch
Fraunces, Inter, and JetBrains Mono from Google Fonts.

## What's here

- `src/app/` — routes: library (`/`), book details (`/books/[id]`),
  voices (`/voices`, `/voices/new`), upload (`/upload`), settings
  (`/settings`), onboarding (`/onboarding`)
- `src/components/layout/` — nav rail, mobile nav, app shell, providers
- `src/components/book/` — cover card, continue-listening rail, hero
  (now with a voice picker and cover image), chapter list (generate
  button wired to the real API, gated on the book having a voice)
- `src/components/voice/` — voice card with real training-status polling
- `src/components/player/` — docked mini-player: owns a real `<audio>`
  element, click-to-seek progress bar, skip ±15s, working sleep timer,
  periodic progress-save to the backend
- `src/hooks/use-playback-store.ts` — Zustand store for playback
  *intent* (what should play, at what speed); actual position comes
  FROM the `<audio>` element via `reportProgress`, not the other way
  around
- `src/hooks/use-books.ts`, `use-voices.ts` — React Query hooks, with
  polling while a chapter is generating or a voice is training
- `src/lib/api.ts` — the backend client
- `src/types/index.ts` — shared domain types, kept in sync with the
  backend's Pydantic schemas

## Design system

- Palette: ink navy background, warm amber accent, quiet teal for
  progress/bookmarks — tokens live in `tailwind.config.ts`
- Type: Fraunces (display/serif) for titles, Inter for UI, JetBrains Mono
  for timestamps
- Signature element: the "ribbon tab" — a diagonal-cut marker on book
  covers and the mini-player, standing in for "where you stopped"
  instead of a generic progress bar (see `.ribbon-tab` in `globals.css`)

## Verified

`npx tsc --noEmit` and `npx next build` both pass clean (Google Fonts
network access aside — some sandboxes' egress allowlists don't include
`fonts.googleapis.com`; on a normal connection this is not an issue).

## Remaining

Milestone 5 — local packaging: full docker-compose (adds Postgres,
Redis, and the frontend itself to the backend + tts-service pair
already running), one-command local setup.
