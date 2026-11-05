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

**Decision:** `Profile` contains `user`, `date_of_birth`, `goal`, `level`, and `excluded_exercises`. Body weight, body measurements, and progress photos will be separate models, each with a date and linked to the user.

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

## 11. Training plan relations are foreign keys

**Date:** 2026-11-05

**Decision:** Every relation in the training plan is a `ForeignKey` on the "many" side:

- `TrainingBlock` → user (`settings.AUTH_USER_MODEL`)
- `PlannedDay` → `TrainingBlock`
- `PlannedExercise` → `PlannedDay`
- `PlannedExercise` → `Exercise`

**Alternatives considered:**

- `OneToOneField` for these relations: would allow only one block per user, one day per block, and one exercise per day.
- A many-to-many field between `PlannedDay` and `Exercise`: the link needs its own data (sets, reps, weight, order), so it is a model of its own. `PlannedExercise` plays the role of the join table, with two foreign keys and extra fields.

**Why:** A user has many blocks over time, a block has several days, and a day has several exercises. One row of `PlannedExercise` refers to exactly one exercise. An exercise appearing in many plans is already covered by the foreign key seen from the other side.

## 12. Days are numbered within the cycle, not tied to weekdays

**Date:** 2026-11-05

**Decision:** `PlannedDay` stores its position in the cycle (day 1, day 2, …), not a day of the week.

**Why:** Users decide which days they train. The cycle is written for a given number of training days per week. The app may suggest how to spread them across the week, but it does not impose a schedule.

## 13. The plan stores targets; progression is computed from logged data

**Date:** 2026-11-05

**Decision:** `PlannedExercise` holds the planned targets only. It has no fields for previous reps or previous weight. Progression is computed by `services` from data the user logs during the block.

**Alternative considered:** Separate rows for every week of the block, with the progression written in advance.

**Why:** Nobody can predict in advance how a user will progress. Results that have already happened belong to the workout log (a separate model, planned for a later stage), for the same reason as decision 8: history must not be overwritten.

## 14. Field types for planned exercises

**Date:** 2026-11-05

**Decision:**

- **Reps** are a range, `reps_min` and `reps_max`, with no separate `reps` field. A fixed number of reps is a range where min equals max. The database will enforce `reps_min <= reps_max` with a check constraint.
- **Weight** is a `DecimalField` with `max_digits=6` and `decimal_places=2`, and it is optional, because some exercises use body weight only. Two decimal places cover the smallest plates (1.25 kg). Four digits before the decimal point are needed to store 1000 kg, the highest realistic load (for example on a leg press).
- **Rest** is stored as a number of seconds in `rest_seconds`, not as a `TimeField`, which stores a time of day. The field cannot be called `break`, because that is a reserved word in Python.
- **Counts** (sets, reps, rest) use positive integer types, so negative values are impossible in the database.
- **Effort** has two optional fields, `rir` and `rpe`. RIR and RPE are two scales for the same thing (RPE ≈ 10 − RIR), and users can plan with whichever they prefer, or with neither. `rir` is a positive integer. `rpe` is a `DecimalField` with `max_digits=3` and `decimal_places=1`, because RPE is commonly used in half steps (7.5, 8.5) and must be able to store 10.0. It is a decimal rather than a float for the same reason as weight.

**Why `DecimalField`:** A float stores numbers in binary, so many decimal fractions cannot be stored exactly. A decimal stores exactly the value that was entered. Weights go up in steps such as 1.25 kg or 2.5 kg and are summed in progression calculations, so exact values matter.

**Known limitation:** `max_digits=6` accepts values up to 9999.99. If weights above 1000 kg should be rejected, that needs a separate check constraint or validator.

## 15. Block dates without redundant fields

**Date:** 2026-11-05

**Decision:** `TrainingBlock` stores `start_date` and `end_date`. The duration is derived from them as the `duration_days` property, which counts both the start and the end date (a block from Monday to Sunday lasts 7 days).

**Why:** Any one of the three can be calculated from the other two. Storing all three lets them drift apart, for example when a block is extended and only the end date is changed.

## 16. Only one active block per user

**Date:** 2026-11-05

**Decision:** A user can have many blocks, but only one of them can be active at a time. This will be enforced in the database by a `UniqueConstraint` with a `condition` on the active flag.

**Alternative considered:** A one-to-one relation between the user and the block. It would forbid a second block altogether, while the goal is only to forbid a second *active* block.

## 17. Deletion behaviour

**Date:** 2026-11-05

**Decision:**

- Deleting a user deletes their blocks (`CASCADE`).
- Deleting a block deletes its days (`CASCADE`).
- Deleting a day deletes its planned exercises (`CASCADE`). A planned exercise has no meaning without its day.
- An `Exercise` from the library cannot be deleted while any plan uses it (`PROTECT`).

**Why `PROTECT`:** Exercises must not silently disappear from plans. That applies to the active block and to archived blocks, which are the user's training history.

**Open question:** Since a used exercise cannot be deleted, the library needs another way to retire exercises, for example an `is_active` flag on `Exercise`.
