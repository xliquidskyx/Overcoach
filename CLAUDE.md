# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Overcoach is an early-stage Django 6.1 project (Python 3.14) on PostgreSQL 18, which runs in Docker Compose. It will be a personal strength-training app: you plan training blocks, log workouts, and have an LLM propose the next block, which explicit rules in code must validate before it is accepted (see the roadmap in `README.md`). So far only the custom user model and the admin exist: `training` is an empty app, and `config/urls.py` routes only `admin/`. There are no tests yet, and no linter or formatter is configured.

## Commands

Dependencies live in `.venv`; run commands with `.venv/bin/python` or activate it first.

```sh
pip install -r requirements.txt

docker compose up -d db                                 # start Postgres (needed for everything below)

python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py check

python manage.py test                                   # all tests
python manage.py test accounts                          # one app
python manage.py test accounts.tests.SomeTestCase.test_x  # one test
```

## Configuration

`config/settings.py` reads its values from a git-ignored `.env` at the repo root through `django-environ`.

- `SECRET_KEY` is required; Django will not start without it.
- `DEBUG` defaults to `False`, so set `DEBUG=True` in `.env` for local work.
- `ALLOWED_HOSTS` is an optional comma-separated list.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` and `POSTGRES_PORT` are all required and have no defaults. The same `.env` is also read by `docker-compose.yml` to create the database, so Django and the container always use the same credentials. The container publishes its port only on `127.0.0.1:5432`, so locally use `POSTGRES_HOST=localhost` and `POSTGRES_PORT=5432`.
- The test runner creates a separate `test_<POSTGRES_DB>` database, so the database user needs the `CREATEDB` privilege. The user that the Postgres image creates is a superuser, so it already has it.

Email uses Django 6.1's `MAILERS` setting, not `EMAIL_BACKEND`, and currently prints to the console.

## Architecture

- `config/` is the project package (settings, root URLs, ASGI/WSGI).
- `accounts/` holds the custom `User` model, set as `AUTH_USER_MODEL = 'accounts.User'`. It extends `AbstractUser` and requires a unique `email`, while `username` remains the login field. Reference it through `settings.AUTH_USER_MODEL` or `get_user_model()`, not `django.contrib.auth.models.User`.
- `training/` is the placeholder for the training domain.

## Deployment

`DEPLOY.md` is the pre-deploy checklist (secret key, `DEBUG`, secure cookies/SSL/HSTS, mailers, `STATIC_ROOT`, `check --deploy`). The settings do not meet it yet, so check it when changing anything related to production.
