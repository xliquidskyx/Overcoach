# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Rules for working in this repo

This is a portfolio project. The author writes models, migrations, business logic and tests herself, and uses Claude Code mainly for review and for boilerplate she explicitly delegates.

- **Never create, edit, delete or apply migrations.** Do not run `makemigrations`, `migrate`, or any command that changes the database schema or its migration history, and do not touch files in `*/migrations/`. If a change needs a migration, say so and stop. (Reason: a migration that was applied to the local database and then removed from the repo left the database out of sync with the code, and the only clean fix was resetting the database.)
- Do not edit models, tests or `conftest.py` unless the task explicitly asks for it. A review only reads code and reports findings; it does not change files.
- Change only the files the task names. If something else needs changing, report it instead.
- Do not run `git commit`, `git stash`, `git checkout` or `git restore`; the author commits herself after reviewing the diff.

## Project status

Overcoach is an early-stage Django 6.1 project (Python 3.14) on PostgreSQL 18, which runs in Docker Compose. It will be a personal strength-training app: you plan training blocks, log workouts, and have an LLM propose the next block, which explicit rules in code must validate before it is accepted (see the roadmap in `README.md`). So far there is the custom user model, the admin, and the training models: `Exercise`, `Profile`, the plan (`TrainingBlock` → `PlannedDay` → `PlannedExercise`), the workout log (`WorkoutSession` → `SetLog`) and `Measurement`. `config/urls.py` routes only `admin/`, and there are no views or service functions yet; login, registration and HTMX workout-logging views are next.

Code is formatted with `ruff format` (installed in `.venv`, but not listed in `requirements-dev.txt` and with no config file, so the defaults apply).

## Commands

Dependencies live in `.venv`; run commands with `.venv/bin/python` / `.venv/bin/pytest` or activate it first.

```sh
pip install -r requirements-dev.txt   # runtime deps (requirements.txt) + pytest, pytest-django

docker compose up -d db               # start Postgres (needed for everything below, tests included)

python manage.py runserver
python manage.py check
python manage.py loaddata exercises   # exercise library from training/fixtures/exercises.json
# makemigrations / migrate: run by the author only (see "Rules for working in this repo")

ruff format .                         # format (ruff defaults)

pytest                                                    # all tests
pytest training                                           # one app
pytest training/tests/test_profile_functions.py::test_user_cannot_have_two_profiles  # one test
```

Tests run with pytest + pytest-django (`pytest.ini` sets `DJANGO_SETTINGS_MODULE = config.settings`), not `manage.py test`. They are plain functions in `<app>/tests/test_*.py`, and a test that touches the database must be marked `@pytest.mark.django_db`.

The root `conftest.py` provides factory fixtures: `make_user`, `make_profile`, `make_exercise`, `make_block`, `make_day`, `make_planned_exercise`, `make_session`, `make_set_log` and `make_measurement`. Each one returns a function that takes field overrides as kwargs, builds any missing parents itself (for example `make_planned_exercise()` creates a day, a block, a user and an exercise), and uses a shared counter so unique fields (`username`, `email`, `Exercise.name`, `position`, `set_number`) don't collide. Use these fixtures instead of creating objects by hand. Pass weights as `Decimal("...")`, never floats.

Testing conventions (reasons in `docs/decisions.md` entry 32):

- A constraint is tested with `pytest.raises(IntegrityError)` around exactly one factory call (see `training/tests/test_plan_constraints.py` and `test_session_constraints.py`). Ranges are tested on both edges: the edge values pass, and the first values outside fail, with `@pytest.mark.parametrize` so each failing value gets its own test and transaction.
- `on_delete` tests (`training/tests/test_sessions_on_delete.py`) check the result in the database with `Model.objects.filter(pk=...).exists()`, not on objects held in variables, and use `refresh_from_db()` to see a `SET_NULL`. Save the `pk` in a variable before calling `delete()`, because `delete()` sets the instance's `pk` to `None`.
- `ProtectedError` is raised by Django before any SQL, so the transaction stays usable; an `IntegrityError` breaks it.

## Configuration

`config/settings.py` reads its values from a git-ignored `.env` at the repo root through `django-environ` (`.env.example` lists every variable).

- `SECRET_KEY` is required; Django will not start without it.
- `DEBUG` defaults to `False`, so set `DEBUG=True` in `.env` for local work.
- `ALLOWED_HOSTS` is an optional comma-separated list.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` and `POSTGRES_PORT` are all required and have no defaults. The same `.env` is also read by `docker-compose.yml` to create the database, so Django and the container always use the same credentials. The container publishes its port only on `127.0.0.1:5432`, so locally use `POSTGRES_HOST=127.0.0.1` and `POSTGRES_PORT=5432`. The `POSTGRES_*` values are applied only when the `postgres_data` volume is first created; changing them later requires `docker compose down -v` (which deletes all data).
- The test database `test_<POSTGRES_DB>` is created by the test run, so the database user needs the `CREATEDB` privilege. The user that the Postgres image creates is a superuser, so it already has it.

Email uses Django 6.1's `MAILERS` setting, not `EMAIL_BACKEND`, and currently prints to the console.

`TIME_ZONE = "Europe/Warsaw"` with `USE_TZ = True`. For "today" use `timezone.localdate()` and for "now" use `timezone.now()`, never `date.today()` / `datetime.now()`.

## Architecture

`docs/decisions.md` records the design decisions and their reasons. Read it before changing models, and add an entry for new decisions in the same format.

- `config/` is the project package (settings, root URLs, ASGI/WSGI).
- `accounts/` holds only authentication. The custom `User` (`AUTH_USER_MODEL = 'accounts.User'`) extends `AbstractUser`, requires an `email`, and keeps `username` as the login field. Reference it through `settings.AUTH_USER_MODEL` or `get_user_model()`, never `django.contrib.auth.models.User`.
  - Email rules are enforced in the database through `Meta.constraints`: `user_email_ci_unique` (a `UniqueConstraint` on `Lower("email")`, so uniqueness ignores letter case) and `user_email_not_empty`. The field itself has no `unique=True`, because the case-insensitive constraint already covers exact duplicates. A duplicate shows up in model forms as a non-field error (`NON_FIELD_ERRORS`), because an expression-based constraint isn't tied to a single field.
  - `accounts/admin.py` subclasses Django's `UserAdmin` and adds `email` to `add_fieldsets`, so users created in the admin always get an email. `accounts/tests/test_admin.py` covers the add form.
  - The required email is enforced by `EmailRequiredUserManager` (`accounts/managers.py`), which overrides `create_user` / `create_superuser` and raises `ValueError` for a missing or blank email. `User.objects.create()`, `save()` and raw SQL bypass this check, so create users through `create_user`.
- `training/` holds the training domain and depends on `accounts`, never the other way round. That is why `Profile` lives here and not in `accounts`.
  - `Exercise` is a shared, curated library with a unique (case-sensitive) `name` and a movement-pattern `category`. Users do not create their own exercises.
  - `Profile` is one-to-one with the user and holds stable data only (goal, level, date of birth, optional `height_cm`, `excluded_exercises`). Exclusions are an M2M on `Profile` (`related_name="excluded_by"`), because they are per user. Data that changes over time goes into separate dated models owned by the user, not into fields on `Profile` (for example `Measurement`).
  - Profiles are created explicitly during onboarding (a planned service function in `training`), never by a `post_save` signal, and `goal` / `level` have no defaults on purpose. A user without a profile is a valid state that means onboarding isn't finished; `user.profile` raises for such users.
  - The training plan is a chain of `ForeignKey`s: user → `TrainingBlock` (`related_name="blocks"`) → `PlannedDay` (`"days"`) → `PlannedExercise` (`"exercises"`), each one deleted with `CASCADE`. `PlannedExercise` → `Exercise` uses `PROTECT`, so an exercise that any plan uses cannot be deleted. Days and planned exercises are ordered by `position`, which is unique within their parent. Days are numbered positions in the cycle, not weekdays.
  - `PlannedExercise` stores only the planned targets: a reps range (`reps_min`/`reps_max`, where a fixed number of reps has min = max), an optional `Decimal` weight, `rest_seconds`, and optional `rir`/`rpe`. It has no fields for actual results; those belong to the planned workout log, and progression will be computed from logged data.
  - The workout log belongs to the user, not to the plan: user → `WorkoutSession` (`related_name="workout_sessions"`, `CASCADE`) → `SetLog` (`"sets"`, `CASCADE`). `WorkoutSession.planned_day` and `SetLog.planned_exercise` are optional and use `SET_NULL`, so deleting a block keeps the history and off-plan workouts or swapped exercises are possible. `SetLog.exercise` is required and uses `PROTECT`. A session's time is only `started_at` (no separate date field); `finished_at` is null while the session is in progress.
  - The database cannot check that a set's `planned_exercise` belongs to its session's `planned_day`, or that the session and the plan have the same owner. The planned logging service function must enforce that.
  - `Measurement` has an FK to the user (not `Profile`), one row per user per `date`, and every value field is optional, but at least one must be filled. It uses `body_weight`, because `weight` means the load in `PlannedExercise` and `SetLog`.
  - Data integrity is enforced in the database through `Meta.constraints`, not only through validators. Plan: one active block per user (a conditional `UniqueConstraint`), `end_date >= start_date`, unique `position` per parent, `reps_max >= reps_min`, `sets > 0`, `reps_min > 0`, `rpe` between 0 and 10, `rir <= 10`, and `weight` between 0 and 1000. Log: `set_number` unique per session and exercise, `set_number > 0`, `reps > 0`, required `weight` between 0 and 1000 (0 for bodyweight), `rir <= 10`, `finished_at >= started_at`, and `body_fat_percent` between 0 and 100. Blocks, sessions and measurements are ordered newest first (`-<date field>`, `-id`); sets by `id` (the order they were logged).
  - The open questions in `docs/decisions.md` are still unresolved: case-insensitive exercise names (10) and how to retire exercises that plans or logs use (17). Entries 18, 28 and 29 list the constraints; `training/models.py` is the source of truth for what is enforced.

## Deployment

`DEPLOY.md` is the pre-deploy checklist (secret key, `DEBUG`, secure cookies/SSL/HSTS, mailers, `STATIC_ROOT`, `check --deploy`). The settings do not meet it yet, so check it when changing anything related to production.
