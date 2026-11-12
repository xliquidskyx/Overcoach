# Overcoach

A personal strength-training app built with Django. The goal is to plan training blocks, log workouts from a phone, track progress and measurements, and use an LLM to propose the next training block from that data. Every proposal is checked against explicit rules in code before it is accepted.

> **Status:** early development. So far the project has a custom user model, the Django admin, and the training models: an exercise library, user profiles, and training plans (blocks, planned days, and planned exercises), and the models for the workout log (sessions and logged sets) and body measurements. The integrity rules of the plan and of the log are enforced as database constraints and covered by tests, including what happens on delete. The admin can edit whole training plans (days and exercises inline) and logged workouts. Login, registration, and the mobile workout-logging views are next.

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
python manage.py loaddata exercises   # exercise library
python manage.py createsuperuser
python manage.py runserver
```

The admin panel is at http://127.0.0.1:8000/admin/. A training block is edited on its own page with its days inline; each day links to a page where its exercises are edited inline, with exercise search. Django has no nested inlines, so a plan is edited on these two levels.

`loaddata exercises` loads the exercise library from `training/fixtures/exercises.json`. Every entry has a fixed primary key, so running the command again updates the same rows instead of adding duplicates.

### Running tests

Tests use pytest with pytest-django and need the database container to be running. Run them from the repository root:

```sh
pytest -v                                    # all tests
pytest training                              # one app
pytest training/tests/test_profile_functions.py::test_user_cannot_have_two_profiles  # one test
```

Test data is created with factory fixtures from the root `conftest.py` (`make_user`, `make_profile`, `make_exercise`, `make_block`, `make_day`, `make_planned_exercise`, `make_session`, `make_set_log`, `make_measurement`). Each factory takes field overrides as keyword arguments and builds any missing parent objects itself, so `make_planned_exercise()` alone creates a whole valid plan chain.

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
accounts/   custom User model (AbstractUser with a required email, unique regardless of letter case)
training/   training domain: exercise library, user profiles, training plans, workout log, body measurements
docs/       design decisions (decisions.md)
```

The custom user model is set from the start (`AUTH_USER_MODEL = "accounts.User"`). Swapping the user model after the first migration is difficult. Training-specific data lives in a separate `Profile` model in the `training` app, linked one-to-one with `User`.

A training plan is a chain of models: a `TrainingBlock` belongs to a user and has a start and end date, it contains `PlannedDay`s numbered by their position in the cycle, and each day contains `PlannedExercise`s that point to an exercise in the shared library. A planned exercise stores only the targets (sets, a reps range, optional weight, rest, optional RIR/RPE). Actual results will go into the workout log, and progression will be computed from them.

The rules a plan must follow are enforced by PostgreSQL through `Meta.constraints`, not only by form validation, so they also hold for data from the shell, the admin, or a future LLM: a user can have only one active block, a block cannot end before it starts, positions are unique within a block or day, and planned values stay in sensible ranges (`reps_max >= reps_min`, at least one set and one rep, RPE 0–10, RIR up to 10, weight 0–1000 kg). The workout log follows the same approach: set numbers are unique per session and exercise, a session cannot finish before it starts, logged values use the same ranges as the plan, and a measurement must record at least one value, at most once per user per day. Deleting an old block keeps its sessions (they only lose the link to the plan), deleting a user deletes all of their data, and an exercise that appears in a logged set cannot be deleted. The reasons behind these and other choices are recorded in [docs/decisions.md](docs/decisions.md).

## Roadmap

- [x] Project setup, custom user model, environment-based settings
- [x] PostgreSQL in Docker Compose
- [x] pytest setup
- [x] Training models: exercises and user profiles
- [x] Training models: training blocks, planned days and exercises
- [x] Database constraints and model tests with factory fixtures
- [x] Admin for training plans (inline days and exercises)
- [ ] Workout logging and measurements, mobile-friendly views
- [ ] REST API with authentication
- [ ] LLM-generated training blocks with rule validation and evals
- [ ] Progress photo comparison as a background task
- [ ] Deployment on a VPS with HTTPS

## Deployment

See [DEPLOY.md](DEPLOY.md) for the pre-deployment checklist.
