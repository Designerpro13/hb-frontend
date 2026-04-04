# Secure CRUD Starter (React + FastAPI)

This starter is a safe alternative to intentionally vulnerable builds.

## Run Backend

1. `cd backend`
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `cp .env.example .env`
5. Set `API_TOKEN` in `.env`
6. Start API from inside backend: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`

Alternative (run from workspace root):

- `source backend/.venv/bin/activate`
- `uvicorn backend.app.main:app --reload --reload-dir backend --host 127.0.0.1 --port 8000`

## Run Frontend

1. `cd frontend`
2. `npm install`
3. `npm run dev`
4. Open `http://127.0.0.1:5173`

Use the same `API_TOKEN` value in the login form.

## Run In GitHub Codespaces

1. Start backend:
- `cd backend`
- `python3 -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt`
- `cp .env.example .env` (first run only)
- Set `API_TOKEN` in `.env`
- `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

2. In a second terminal, start frontend:
- `cd frontend`
- `npm install`
- `npm run dev`

3. In the Ports panel:
- Open port `5173` in browser.
- Keep visibility as `Private` unless you intentionally need public access.

Notes:
- Frontend requests to `/api` and `/health` are proxied to backend port `8000`.
- If you want frontend to call backend directly instead of proxy, set `VITE_API_BASE` to your forwarded backend URL before starting frontend.

## Files

- `backend/app/main.py`: API endpoints and security middleware.
- `frontend/src/App.jsx`: token login and CRUD client.
- `OWASP_IMPLEMENTATION_PLAN.md`: frontend/backend security mapping including common misconfigurations.
