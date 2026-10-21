# Infra

Local-development-only configuration. This project is local-first and
is not intended for cloud deployment.

- `backend/.env.example`: settings for running the backend outside Docker
- `frontend/.env.local.example`: API address for `npm run dev`
- `docker/docker-compose.yml`: the full local stack (sets everything itself)
