# CareerCompass

CareerCompass is an AI career guidance chatbot with **Flask + LangChain**, now upgraded with:
- **Persistent user/chat storage in PostgreSQL**
- **Redis-backed rate limiting and session metadata cache**
- **Token-based authentication**
- **Tier-based usage controls** (`free`, `pro`, `enterprise`)

## Architecture
- **Flask app**: API + chat UI
- **PostgreSQL**: users, chat sessions, chat messages
- **Redis**: per-user/per-endpoint rate counters + cached session preview
- **LLM providers via LangChain**: OpenAI or Gemini

## Quickstart

### 1) Start services
```bash
docker run --name cc-postgres -e POSTGRES_USER=career -e POSTGRES_PASSWORD=career -e POSTGRES_DB=career_compass -p 5432:5432 -d postgres:16

docker run --name cc-redis -p 6379:6379 -d redis:7
```

### 2) Python setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 3) Configure `.env`
Use `.env.example` and set keys:
```bash
APP_ENV=development
SECRET_KEY=replace-me
DATABASE_URL=postgresql+psycopg://career:career@localhost:5432/career_compass
REDIS_URL=redis://localhost:6379/0
TOKEN_TTL_SECONDS=604800

LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

### 4) Run app
```bash
python run.py
```

## Auth and tier model

### Register
`POST /api/auth/register`
```json
{
  "email": "user@example.com",
  "password": "strongpassword",
  "tier": "free"
}
```

### Login
`POST /api/auth/login`
```json
{
  "email": "user@example.com",
  "password": "strongpassword"
}
```

Response includes `access_token`.

Use token in authenticated routes:
```http
Authorization: Bearer <access_token>
```

## Chat/session APIs
- `GET /api/sessions` → list all sessions for authenticated user
- `POST /api/chat` with:
```json
{
  "message": "Help me switch to product management",
  "session_id": 12
}
```
If `session_id` is omitted, a new persistent session is created.

## Tier-based rate limits
Per user, per endpoint, per minute:
- `free`: 10 requests/min
- `pro`: 60 requests/min
- `enterprise`: 300 requests/min

Stored and enforced through Redis counters.

## Production run
```bash
gunicorn -w 2 -k gthread -b 0.0.0.0:5000 "run:app"
```

## Health
`GET /health` returns app/DB/Redis status.

## Tests
```bash
pytest
```
