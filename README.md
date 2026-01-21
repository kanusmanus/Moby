# MobyPark 🅿️  
**FastAPI + SQLAlchemy + Alembic + PostgreSQL + Redis (Dockerized)**

A clean, production-ready backend for a parking platform — with authentication, migrations, and Docker-based development.

This guide helps any teammate set up and run the project from a completely clean environment.

---

## 🧭 Table of Contents
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
  - [.env](#env)
  - [`alembic.ini`](#alembicini)
- [First Run (Docker)](#first-run-docker)
- [Migrations (Alembic)](#migrations-alembic)
  - [Create a migration from models](#create-a-migration-from-models)
  - [Apply migrations](#apply-migrations)
  - [Upgrade to head (after model changes)](#upgrade-to-head-after-model-changes)
  - [Inspect the DB](#inspect-the-db)
- [Development Workflow](#development-workflow)
  - [Live reload](#live-reload)
  - [When requirements.txt changes](#when-requirementstxt-changes)
  - [Resetting the database](#resetting-the-database)
- [API Quickstart](#api-quickstart)
- [Common Pitfalls](#common-pitfalls)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Optional Enhancements](#optional-enhancements)

---

## 🧩 Prerequisites

- **Docker** and **Docker Compose** installed (Compose v2 → `docker compose`).
- No local Python installation required; everything runs inside Docker.

---

## 🗂 Project Structure

```text
mobypark/
├─ app/
│  ├─ main.py                 # FastAPI entrypoint
│  ├─ routers/
│  │  └─ auth.py              # /auth endpoints (register, login, users)
│  ├─ models/
│  │  ├─ __init__.py          # imports models to populate Base.metadata
│  │  ├─ user.py              # User ORM model
│  │  └─ reservation.py       # Example model
│  ├─ schemas/                # Pydantic v2 schemas (RegisterIn/Out, LoginIn/Out, UserOut)
│  ├─ services/security.py    # Password hashing & JWT helpers
│  ├─ db/
│  │  ├─ base.py              # Declarative Base + imports of all models
│  │  ├─ session.py           # Async session factory / get_session()
│  │  └─ ...
│  └─ core/config.py          # Settings (Pydantic BaseSettings)
├─ migrations/
│  ├─ env.py                  # Alembic env (uses DATABASE_URL)
│  └─ versions/               # Auto-generated migration scripts
├─ alembic.ini                # Alembic config
├─ docker-compose.yml
├─ requirements.txt
└─ .env                       # Local secrets & config (ignored by Git)
```

---

## ⚙️ Configuration

### `.env`

Create a `.env` file in the project root.

> ⚠️ **Important:** No inline comments (`#`) on the same line as values.

```dotenv
# --- PostgreSQL ---
POSTGRES_USER=app
POSTGRES_PASSWORD=change_me_strong
POSTGRES_DB=parking

# --- App runtime ---
APP_HOST=0.0.0.0
APP_PORT=8000
APP_WORKERS=4

# --- Redis (optional) ---
REDIS_HOST=redis
REDIS_PORT=6379

# --- Security ---
PASSWORD_PEPPER=add_a_long_random_string_here
JWT_SECRET=replace_with_long_random_string
JWT_ALG=HS256
JWT_EXP_MIN=30

# --- Database URLs (psycopg v3 driver) ---
DATABASE_HOST=db
DATABASE_PORT=5432
DATABASE_NAME=${POSTGRES_DB}
DATABASE_USER=${POSTGRES_USER}
DATABASE_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgresql+psycopg://${DATABASE_USER}:${DATABASE_PASSWORD}@${DATABASE_HOST}:${DATABASE_PORT}/${DATABASE_NAME}
```

---

### `alembic.ini`

Ensure Alembic uses the same DB URL as the app.

```ini
[alembic]
script_location = migrations
sqlalchemy.url = ${DATABASE_URL}

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers = console
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

---

## 🚀 First Run (Docker)

```bash
docker compose up -d
# or to see logs live
docker compose up
```

Services started:
- API → http://localhost:8000  
- Docs → http://localhost:8000/docs  
- Postgres → service `db`  
- Redis → service `redis`

---

## 🧱 Migrations (Alembic)

### Create a migration from models

```bash
docker compose exec api alembic revision --autogenerate -m "describe your change"
```

### Apply migrations

```bash
docker compose exec api alembic upgrade head
```

### Upgrade to head (after model changes)

```bash
docker compose exec api alembic revision --autogenerate -m "add field X to table Y"
docker compose exec api alembic upgrade head
```

### Inspect the DB

```bash
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\dt'
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'select * from alembic_version;'
```

---

## 💻 Development Workflow

### Live reload

Uvicorn runs with `--reload`, so code changes apply instantly.

### When `requirements.txt` changes

```bash
docker compose build api
docker compose up -d
```

### Resetting the database

```bash
docker compose down -v
docker compose up -d
docker compose exec api alembic upgrade head
```

---

## 🧪 API Quickstart

```bash
curl http://localhost:8000/health
```

**Docs:** http://localhost:8000/docs

**Register:**
```http
POST /auth/register
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "mysecretpassword",
  "name": "John Doe"
}
```

**Login:**
```http
POST /auth/login
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "mysecretpassword"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

## ⚠️ Common Pitfalls

- 404 on `/register` → Use `/auth/register`
- GET with body → Not allowed
- Inline comments in `.env` → ❌
- Migrations missing → `alembic upgrade head`
- Psycopg2 errors → Fix driver in `alembic.ini`
- Rebuild image after dependency changes

---

## 🔒 Security Notes

- Hash passwords (Argon2 / bcrypt)
- Never store plaintext passwords
- Use strong `JWT_SECRET`
- Return same message for invalid login
- Use HTTPS in production

---

## 🧰 Troubleshooting

```bash
docker compose logs -f api
docker compose exec api printenv | sort
docker compose exec api python -c "import os; print(os.getenv('DATABASE_URL'))"
```

Verify DB connectivity:

```bash
docker compose exec api python - <<'PY'
import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine
url = os.getenv("DATABASE_URL")
async def main():
    eng = create_async_engine(url)
    async with eng.connect() as conn:
        res = await conn.execute("select 1")
        print("DB OK:", list(res))
asyncio.run(main())
PY
```

---

## 🧪 Optional Enhancements

```makefile
up:
	docker compose up -d
logs:
	docker compose logs -f api
mig:
	docker compose exec api alembic revision --autogenerate -m "update"
head:
	docker compose exec api alembic upgrade head
down:
	docker compose down
nuke:
	docker compose down -v
rebuild:
	docker compose build --no-cache api && docker compose up -d
```

---

✅ **You’re ready to go!**  
Run:
```bash
docker compose up -d
docker compose exec api alembic upgrade head
```
Then open [http://localhost:8000/docs](http://localhost:8000/docs)



