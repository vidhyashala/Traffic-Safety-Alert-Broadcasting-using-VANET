# Deployment Guide (Full Project)

## Option A: Local full deployment

```bash
./deploy/deploy_local.sh
```

Deployment link (local):
- http://127.0.0.1:8000/docs

## Option B: Docker deployment

```bash
docker compose up --build
```

Deployment link (local Docker):
- http://127.0.0.1:8000/docs

## Option C: Render cloud deployment

1. Push this repository to GitHub.
2. In Render, create a **Blueprint** deployment and point it to this repo.
3. Render will use `deploy/render.yaml`.
4. After deployment, your public link will be:
   - `https://vanet-alert-api.onrender.com/docs` (or Render-generated service URL)

## Notes
- Train the model first (`python/train_alert_model.py`) so `/predict` can return priority.
- SUMO/OMNeT++ components remain part of the project execution workflow and are documented in README.
