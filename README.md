# CareerCompass

CareerCompass is a production-oriented AI career guidance chatbot built with **Flask**, **LangChain**, and pluggable LLM providers (**OpenAI** or **Gemini**).

## Features
- Flask API + lightweight chat UI.
- Provider abstraction for OpenAI and Gemini via LangChain.
- Prompted career-coach behavior with context-aware chat history.
- Input validation with Pydantic.
- Health endpoint for deployments.
- Fallback mode when API keys are not configured.

## Quickstart (Basics)

### 1) Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 2) Configure environment
Create `.env`:
```bash
APP_ENV=development
SECRET_KEY=replace-me
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
# OR for Gemini:
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=your_key_here
# GEMINI_MODEL=gemini-1.5-flash
```

### 3) Run locally
```bash
python run.py
```
Visit: `http://localhost:5000`

## API
### `POST /api/chat`
Request:
```json
{
  "message": "I want to become a data analyst in 6 months.",
  "history": [
    {"user": "...", "assistant": "..."}
  ]
}
```

Response:
```json
{
  "reply": "...",
  "provider": "openai",
  "model": "gpt-4o-mini"
}
```

### `GET /health`
Returns service status and environment.

## Production-ready setup

### Gunicorn
```bash
gunicorn -w 2 -k gthread -b 0.0.0.0:5000 "run:app"
```

### Docker
```bash
docker build -t career-compass .
docker run --env-file .env -p 5000:5000 career-compass
```

### Recommended next hardening
- Add persistent user/session storage (PostgreSQL + Redis).
- Add auth + rate limiting.
- Add observability (structured logs, tracing, metrics).
- Add moderation and policy guardrails.
- Add CI/CD deployment pipeline.

## Testing & lint
```bash
pytest
ruff check .
```
