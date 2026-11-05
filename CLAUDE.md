# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Overcoach is an early-stage Django 6.1 project (Python 3.14) on PostgreSQL 18, which runs in Docker Compose. It will be a personal strength-training app: you plan training blocks, log workouts, and have an LLM propose the next block, which explicit rules in code must validate before it is accepted (see the roadmap in `README.md`). So far there is the custom user model, the admin, and the first training models (`Exercise`, `Profile`). `config/urls.py` routes only `admin/`, and there are no views yet. No linter or formatter is configured.

## Commands

Dependencies live in `.venv`; run commands with `.venv/bin/python` / `.venv/bin/pytest` or activate it first.

```sh
pip install -r requirements-dev.txt   # runtime deps (requirements.txt) + pytest, pytest-django

docker compose up -d db               # start Postgres (needed for everything below, tests included)

python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py check

pytest                                                    # all tests
pytest training                                           # one app
pytest training/tests/test_profile_functions.py::test_user_cannot_have_two_profiles  # one test
```

Tests run with pytest + pytest-django (`pytest.ini` sets `DJANGO_SETTINGS_MODULE = config.settings`), not `manage.py test`. They are plain functions in `<app>/tests/test_*.py`, and a test that touches the database must be marked `@pytest.mark.django_db`.

## Configuration

`config/settings.py` reads its values from a git-ignored `.env` at the repo root through `django-environ` (`.env.example` lists every variable).

- `SECRET_KEY` is required; Django will not start without it.
- `DEBUG` defaults to `False`, so set `DEBUG=True` in `.env` for local work.
- `ALLOWED_HOSTS` is an optional comma-separated list.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` and `POSTGRES_PORT` are all required and have no defaults. The same `.env` is also read by `docker-compose.yml` to create the database, so Django and the container always use the same credentials. The container publishes its port only on `127.0.0.1:5432`, so locally use `POSTGRES_HOST=127.0.0.1` and `POSTGRES_PORT=5432`. The `POSTGRES_*` values are applied only when the `postgres_data` volume is first created; changing them later requires `docker compose down -v` (which deletes all data).
- The test database `test_<POSTGRES_DB>` is created by the test run, so the database user needs the `CREATEDB` privilege. The user that the Postgres image creates is a superuser, so it already has it.

Email uses Django 6.1's `MAILERS` setting, not `EMAIL_BACKEND`, and currently prints to the console.

## Architecture

`docs/decisions.md` records the design decisions and their reasons. Read it before changing models, and add an entry for new decisions in the same format.

- `config/` is the project package (settings, root URLs, ASGI/WSGI).
- `accounts/` holds only authentication. The custom `User` (`AUTH_USER_MODEL = 'accounts.User'`) extends `AbstractUser`, requires a unique `email`, and keeps `username` as the login field. Reference it through `settings.AUTH_USER_MODEL` or `get_user_model()`, never `django.contrib.auth.models.User`.
  - The required email is enforced by `EmailRequiredUserManager` (`accounts/managers.py`), which overrides `create_user` / `create_superuser` and raises `ValueError` for a missing or blank email. `User.objects.create()`, `save()` and raw SQL bypass this check, so create users through `create_user`.
- `training/` holds the training domain and depends on `accounts`, never the other way round. That is why `Profile` lives here and not in `accounts`.
  - `Exercise` is a shared, curated library with a unique (case-sensitive) `name` and a movement-pattern `category`. Users do not create their own exercises.
  - `Profile` is one-to-one with the user and holds stable data only (goal, level, date of birth, `excluded_exercises`). Exclusions are an M2M on `Profile` (`related_name="excluded_by"`), because they are per user. Data that changes over time (weight, measurements, progress photos) goes into separate dated models, not into fields on `Profile`.
  - Profiles are created explicitly during onboarding (a planned service function in `training`), never by a `post_save` signal, and `goal` / `level` have no defaults on purpose. A user without a profile is a valid state that means onboarding isn't finished; `user.profile` raises for such users.

## Deployment

`DEPLOY.md` is the pre-deploy checklist (secret key, `DEBUG`, secure cookies/SSL/HSTS, mailers, `STATIC_ROOT`, `check --deploy`). The settings do not meet it yet, so check it when changing anything related to production.
