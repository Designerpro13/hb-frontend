# Vulnerable CRUD Lab (React + FastAPI)

This repository intentionally contains insecure patterns for security scanner validation and controlled testing.

Use only in authorized lab environments.

## Project Structure

- `backend/`: FastAPI application
- `frontend/`: Vite + React client
- `VULNERABILITIES.md`: concise vulnerability inventory
- `OWASP_IMPLEMENTATION_PLAN.md`: secure-baseline reference (opposite direction)

## Local Run

### Backend

1. `cd backend`
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`

### Frontend

1. `cd frontend`
2. `npm install`
3. `npm run dev`
4. Open `http://127.0.0.1:5173`

Notes:
- Frontend uses clear-text login fields (`username`, `password`) and stores `access_token` in `localStorage`.
- Frontend proxy routes `/api` and `/health` to backend port `8000` via `frontend/vite.config.js`.
- Optional direct backend mode: set `VITE_API_BASE` before `npm run dev`.

## Current Login Behavior

Backend login endpoint: `POST /api/login`

Accepted weak credentials include:
- `admin` / `admin123456`
- `test` / `password123`
- empty username and/or empty password

## Scanner Targets

Useful endpoints for Nessus, Nikto, Nmap, ZAP, and static analyzers:

- `GET /health`
- `GET /admin`
- `GET /api/debug`
- `GET /api/items`
- `GET /api/items/{id}`
- `GET /api/user/{id}`
- `GET /api/search?q=...`
- `POST /api/login`
- `POST /api/items`
- `PUT /api/items/{id}`
- `DELETE /api/items/{id}`

## Deployment Notes

- Frontend: Vercel (root directory `frontend`)
- Backend: Render or Railway (root directory `backend`)
- Set frontend env var `VITE_API_BASE` to deployed backend URL

## Disclaimer

Do not deploy this application in production or expose it to untrusted networks.
