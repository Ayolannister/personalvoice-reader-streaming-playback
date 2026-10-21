# Docker

One command runs the whole app locally: Postgres, the FastAPI backend,
the XTTS v2 TTS service (Python 3.11) and the Next.js frontend.

## Start

1. `cd docker`
2. `docker compose up --build`
3. Open http://localhost:3000

The first real voice clone downloads the XTTS v2 model (about 2GB) into
the `xtts-models` volume, so it is slow once and fast afterwards.

## Run without the model

To try the full app instantly with silent placeholder audio:

1. `cd docker`
2. `TTS_ENGINE=dummy docker compose up --build`

## Ports

| Service     | URL                          |
|-------------|------------------------------|
| frontend    | http://localhost:3000        |
| backend     | http://localhost:8000/docs   |
| tts-service | http://localhost:8001/health |
| postgres    | localhost:5432               |

## Data

Books, voices, generated audio and the database live in named volumes
(`app-storage`, `pg-data`, `xtts-models`) and survive restarts.

1. Stop: `docker compose down`
2. Stop and wipe everything: `docker compose down -v`

Redis is not included because nothing in the code uses it yet.
