# Overcoach

A personal strength-training app built with Django. The goal is to plan training blocks, log workouts from a phone, track progress and measurements, and use an LLM to propose the next training block from that data. Every proposal is checked against explicit rules in code before it is accepted.

> **Status:** early development. So far the project has a custom user model and the Django admin. The training domain is being built now.

## Tech stack

**Current:** Python 3.14, Django 6.1, django-environ, SQLite (local development only)

**Planned:** PostgreSQL (Docker Compose), pytest, Django REST Framework, HTMX, Celery + Redis, Anthropic API, Caddy on a VPS

## Getting started

Requirements: Python 3.14 and git.

```sh
git clone <repo-url>
cd overcoach

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Generate a secret key and paste it into .env as SECRET_KEY:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The admin panel is at http://127.0.0.1:8000/admin/.

## Configuration

Settings are read from a `.env` file in the repository root. The file is ignored by git, and `.env.example` lists every variable.

| Variable | Required | Description |
| --- | --- | --- |
| `SECRET_KEY` | yes | Django secret key. Use a unique, random value per environment. |
| `DEBUG` | no | Defaults to `False`. Set `DEBUG=True` for local development. |
| `ALLOWED_HOSTS` | no | Comma-separated list of hosts, e.g. `localhost,127.0.0.1`. |

## Project structure

```
config/     project settings, root URLs, ASGI/WSGI
accounts/   custom User model (AbstractUser with a unique, required email)
training/   training domain: exercises, training blocks, workout logs (in progress)
```

The custom user model is set from the start (`AUTH_USER_MODEL = "accounts.User"`). Swapping the user model after the first migration is difficult. Training-specific data will live in a separate `Profile` model linked one-to-one with `User`.

## Roadmap

- [x] Project setup, custom user model, environment-based settings
- [ ] PostgreSQL in Docker Compose, pytest setup
- [ ] Training models: exercises, training blocks, planned days and exercises
- [ ] Workout logging and measurements, mobile-friendly views
- [ ] REST API with authentication
- [ ] LLM-generated training blocks with rule validation and evals
- [ ] Progress photo comparison as a background task
- [ ] Deployment on a VPS with HTTPS

## Deployment

See [DEPLOY.md](DEPLOY.md) for the pre-deployment checklist.
