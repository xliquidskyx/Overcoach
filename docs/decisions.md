# Design decisions

A short record of the design decisions in Overcoach and the reasons behind them. Each entry lists the alternatives that were considered.

## 1. Custom user model from the start

**Date:** 2026-11-02

**Decision:** `accounts.User` extends `AbstractUser` and is set as `AUTH_USER_MODEL` before the first migration. Email is required and unique. Users still log in with their username.

**Why:** Swapping the user model after the first migration is a well-known pain point in Django. It usually means resetting the database. Setting it up on day one takes a few minutes and keeps the model open to future changes.

## 2. PostgreSQL in Docker Compose

**Date:** 2026-11-03

**Decision:** The database runs in a Docker Compose service with a named volume. For now, Django runs on the host and connects to the container.

**Why:** Development runs on the same database engine as production, which SQLite cannot offer. The named volume keeps data when the container is recreated.

## 3. Separate development dependencies

**Date:** 2026-11-04

**Decision:** `requirements.txt` holds runtime dependencies only. `requirements-dev.txt` includes it via `-r requirements.txt` and adds development tools such as pytest and pytest-django. Packages are added by hand rather than with `pip freeze`.

**Why:** The production image stays smaller and has a smaller attack surface, because every unused package is a potential vulnerability. The runtime file also shows exactly what the application depends on.

## 4. pytest with pytest-django

**Date:** 2026-11-04

**Decision:** Tests run with pytest and pytest-django. Configuration lives in `pytest.ini` at the repository root.

**Why:** Plain `assert` statements, fixtures, and `pytest.raises` keep tests short and readable. Database access is opt-in per test, so it is always clear which tests touch the database.

## 5. Email enforced by a custom user manager

**Date:** 2026-11-04

**Context:** `create_user` does not run model validation. A user without an email was saved successfully, and only a second user without an email failed, by accident, on the `UNIQUE` constraint, because both had an empty string as their email.

**Decision:** `EmailRequiredUserManager` extends Django's `UserManager` and overrides `create_user` and `create_superuser`, keeping their original signatures. Both reject a missing, empty, or whitespace-only email with a `ValueError` and pass the email on with surrounding whitespace stripped.

**Alternatives considered:**

- Extending `BaseUserManager`: would mean re-implementing behaviour that `UserManager` already provides.
- Overriding the private `_create_user`: relies on Django internals.

**Known limitation:** The manager only guards the `create_user` / `create_superuser` path. `User.objects.create()`, `save()` after editing a user, and raw SQL bypass it. A database-level constraint would close that gap.

## 6. Excluded exercises as a many-to-many relation on Profile

**Date:** 2026-11-04

**Decision:** Excluded exercises are a many-to-many field on `Profile` pointing to `Exercise`, not a field on `Exercise`.

**Why:** `Exercise` is a shared dictionary. The same exercise can be excluded by some users and not by others, so exclusion belongs to the user, not to the exercise.

## 7. Profile lives in the training app

**Date:** 2026-11-04

**Decision:** `Profile` (one-to-one with `User`) is defined in `training`, not in `accounts`.

**Why:** The profile holds training data: goal, level, and excluded exercises. If it lived in `accounts`, its relation to `Exercise` would make `accounts` depend on `training`, while `training` already depends on the user. That is a circular dependency between apps. With `Profile` in `training`, dependencies point one way (`training` → `accounts`), and `accounts` stays responsible for authentication only.

## 8. Profile holds stable data only

**Date:** 2026-11-04

**Decision:** `Profile` contains `user`, `goal`, `level`, and `excluded_exercises`. Body weight, body measurements, and progress photos will be separate models, each with a date and linked to the user.

**Why:** Weight, measurements, and photos change over time, and tracking progress is the core of the app. Storing them as single fields on the profile would overwrite history and keep only the latest value.

## 9. Profiles are created explicitly, not by a signal

**Date:** 2026-11-04

**Decision:** A profile is created explicitly by a service function in `training` that takes the user and the onboarding data. That is the only place in the code that creates profiles. `goal` and `level` are required fields with no defaults. Later, views that need a profile will redirect users without one to onboarding.

**Alternative considered:** A `post_save` signal on `User` (checking `created`) that creates a profile with default values (goal: muscle building, level: beginner).

**Why explicit creation wins:**

- Default values would be made-up data. If onboarding were skipped, the AI would generate a plan from values the user never gave. A missing profile is an honest, checkable state: onboarding is not finished.
- Without defaults, the database guarantees that every profile is complete.
- Profile creation is visible where it happens. A signal would silently create profiles from tests, the admin, and `createsuperuser`, and it does not fire on `bulk_create`.

**Trade-off:** Accessing `user.profile` for a user without a profile raises an exception, which has to be handled in one place: the redirect to onboarding.

## 10. Exercise names are unique; exercises come from a curated library

**Date:** 2026-11-04

**Decision:** `Exercise.name` is unique. The app ships with a curated library of exercises that users choose from, rather than users creating their own.

**Open question:** `unique=True` is case-sensitive in PostgreSQL, so "Squat" and "squat" can both be saved. Case-insensitive uniqueness still needs to be decided. If users are ever allowed to add their own exercises, uniqueness will need to be scoped per user instead of global.
