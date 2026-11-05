# Overcoach

A personal strength-training app built with Django. The goal is to plan training blocks, log workouts from a phone, track progress and measurements, and use an LLM to propose the next training block from that data. Every proposal is checked against explicit rules in code before it is accepted.

> **Status:** early development. So far the project has a custom user model, the Django admin, and the training models: an exercise library, user profiles, and training plans (blocks, planned days, and planned exercises). Workout logging is next.

## Tech stack

**Current:** Python 3.14, Django 6.1, django-environ, PostgreSQL 18 (Docker Compose), psycopg 3, pytest + pytest-django

**Planned:** Django REST Framework, HTMX, Celery + Redis, Anthropic API, Caddy on a VPS

## Getting started

Requirements: Python 3.14, git, and Docker with Docker Compose.

```sh
git clone <repo-url>
cd overcoach

python3 -m venv .venv
source .venv/bin/activate
# Runtime dependencies plus development tools (pytest, pytest-django):
pip install -r requirements-dev.txt

cp .env.example .env
# Generate a secret key and paste it into .env as SECRET_KEY:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Generate a database password and paste it into .env as POSTGRES_PASSWORD,
# then set POSTGRES_DB and POSTGRES_USER to names of your choice:
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Start PostgreSQL in the background (needed before any manage.py command):
docker compose up -d db

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The admin panel is at http://127.0.0.1:8000/admin/.

### Running tests

Tests use pytest with pytest-django and need the database container to be running. Run them from the repository root:

```sh
pytest -v                                    # all tests
pytest training                              # one app
pytest training/tests/test_profile_functions.py::test_user_cannot_have_two_profiles  # one test
```

Code is formatted with `ruff format .` (default settings).

pytest-django creates a separate `test_<POSTGRES_DB>` database for the run, so the database user needs the `CREATEDB` privilege. The user created by the Postgres image is a superuser, so it already has it.

The database runs in a container, and its data is kept in the named volume `postgres_data`, so it survives `docker compose down`. Running `docker compose down -v` deletes the volume and all data in it.

The `POSTGRES_*` variables are applied only when the volume is empty, on the container's first start. If you change them later, the existing database keeps the old values; remove the volume and start again to recreate it.

## Configuration

Settings are read from a `.env` file in the repository root. The file is ignored by git, and `.env.example` lists every variable.

| Variable | Required | Description |
| --- | --- | --- |
| `SECRET_KEY` | yes | Django secret key. Use a unique, random value per environment. |
| `DEBUG` | no | Defaults to `False`. Set `DEBUG=True` for local development. |
| `ALLOWED_HOSTS` | no | Comma-separated list of hosts, e.g. `localhost,127.0.0.1`. |
| `POSTGRES_DB` | yes | Database name. Read by both Docker Compose and Django. |
| `POSTGRES_USER` | yes | Database user. Read by both Docker Compose and Django. |
| `POSTGRES_PASSWORD` | yes | Database password. Read by both Docker Compose and Django. |
| `POSTGRES_HOST` | yes | Read by Django only. Use `127.0.0.1`, because the container publishes its port only on the local machine. |
| `POSTGRES_PORT` | yes | Read by Django only. The host-side port from `docker-compose.yml`, `5432` by default. |

Docker Compose reads the same `.env` file, so Django and the database container always use the same credentials.

## Project structure

```
config/     project settings, root URLs, ASGI/WSGI
accounts/   custom User model (AbstractUser with a unique, required email)
training/   training domain: exercise library, user profiles, training plans (workout logs to come)
docs/       design decisions (decisions.md)
```

The custom user model is set from the start (`AUTH_USER_MODEL = "accounts.User"`). Swapping the user model after the first migration is difficult. Training-specific data lives in a separate `Profile` model in the `training` app, linked one-to-one with `User`.

A training plan is a chain of models: a `TrainingBlock` belongs to a user and has a start and end date, it contains `PlannedDay`s numbered by their position in the cycle, and each day contains `PlannedExercise`s that point to an exercise in the shared library. A planned exercise stores only the targets (sets, a reps range, optional weight, rest, optional RIR/RPE). Actual results will go into the workout log, and progression will be computed from them. The reasons behind these and other choices are recorded in [docs/decisions.md](docs/decisions.md).

## Roadmap

- [x] Project setup, custom user model, environment-based settings
- [x] PostgreSQL in Docker Compose
- [x] pytest setup
- [x] Training models: exercises and user profiles
- [x] Training models: training blocks, planned days and exercises
- [ ] Workout logging and measurements, mobile-friendly views
- [ ] REST API with authentication
- [ ] LLM-generated training blocks with rule validation and evals
- [ ] Progress photo comparison as a background task
- [ ] Deployment on a VPS with HTTPS

## Deployment

See [DEPLOY.md](DEPLOY.md) for the pre-deployment checklist.
