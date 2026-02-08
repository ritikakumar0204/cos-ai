# AI MCP Hackathon

A full-stack prototype for **organization memory + decision intelligence** with an MCP-style tool API.

## What this project does

- Tracks decisions, versions, stakeholders, and alignment state across projects.
- Exposes scenario and tool endpoints for orchestration workflows.
- Provides a React dashboard for project briefing, meetings, decision evolution, and alignment.
- Supports ElevenLabs-backed text-to-speech and speech-to-text routes.

## Repository layout

- `backend/`: FastAPI service, orchestration agents, MCP routes, decision graph logic, demo data.
- `frontend/`: Vite + React + TypeScript dashboard.
- `tests/`: backend API and behavior tests.
- `docs/`, `infrastructure/`, `shared/`: supporting project folders.

## Prerequisites

- Python 3.11+
- Node.js 18+

## Backend setup (FastAPI)

```bash
# from repo root
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install fastapi uvicorn pydantic pydantic-settings networkx python-multipart pytest

uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend health check:

- `GET http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/docs`

### Backend environment

The service reads `MCP_`-prefixed environment variables (see `backend/app/config.py`):

- `MCP_ELEVENLABS_API_KEY`
- `MCP_ELEVENLABS_VOICE_ID`
- `MCP_ELEVENLABS_MODEL_ID`
- `MCP_ELEVENLABS_STT_MODEL_ID`

## Frontend setup (Vite + React)

```bash
# from repo root
cd frontend
npm install
npm run dev
```

Default app URL:

- `http://localhost:5173`

If your backend runs on a different host/port, set:

- `VITE_API_BASE_URL` (defaults to `http://localhost:8000`)

## Running tests

Backend tests:

```bash
# from repo root (with venv active)
pytest -q
```

Frontend tests:

```bash
cd frontend
npm test
```

## Key API surfaces

- `GET /projects/{project_id}/brief`
- `GET /projects/{project_id}/meetings`
- `POST /projects/{project_id}/meetings/{meeting_id}/review`
- `GET /projects/{project_id}/decisions`
- `GET /projects/{project_id}/alignment`
- `GET /mcp/tools`
- `POST /mcp/tools/{tool_name}`
- `POST /mcp/scenarios/*`
- `POST /query/`
- `POST /tts/elevenlabs`
- `POST /tts/elevenlabs/transcribe`

## Notes

- Demo state is reset when the backend app starts.
- Frontend and backend can run independently during local development.
