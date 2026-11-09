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

**Known limitation (resolved in 22):** The manager only guards the `create_user` / `create_superuser` path. `User.objects.create()`, `save()` after editing a user, and raw SQL bypass it. Database constraints now close that gap; the manager stays for its clear `ValueError` at creation time.

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

- **Reps** are a range, `reps_min` and `reps_max`, with no separate `reps` field. A fixed number of reps is a range where min equals max. The database enforces `reps_max >= reps_min` with a check constraint (see 18).
- **Weight** is a `DecimalField` with `max_digits=6` and `decimal_places=2`, and it is optional, because some exercises use body weight only. Two decimal places cover the smallest plates (1.25 kg). Four digits before the decimal point are needed to store 1000 kg, the highest realistic load (for example on a leg press).
- **Rest** is stored as a number of seconds in `rest_seconds`, not as a `TimeField`, which stores a time of day. The field cannot be called `break`, because that is a reserved word in Python.
- **Counts** (sets, reps, rest) use positive integer types, so negative values are impossible in the database.
- **Effort** has two optional fields, `rir` and `rpe`. RIR and RPE are two scales for the same thing (RPE ≈ 10 − RIR), and users can plan with whichever they prefer, or with neither. `rir` is a positive integer of at most 10. `rpe` is a `DecimalField` with `max_digits=3` and `decimal_places=1`, because RPE is commonly used in half steps (7.5, 8.5) and must be able to store 10.0. It is a decimal rather than a float for the same reason as weight.

**Why `DecimalField`:** A float stores numbers in binary, so many decimal fractions cannot be stored exactly. A decimal stores exactly the value that was entered. Weights go up in steps such as 1.25 kg or 2.5 kg and are summed in progression calculations, so exact values matter.

**Range:** `max_digits=6` alone would accept values up to 9999.99, so a check constraint limits weight to 0–1000 kg (see 18).

## 15. Block dates without redundant fields

**Date:** 2026-11-05

**Decision:** `TrainingBlock` stores `start_date` and `end_date`. The duration is derived from them as the `duration_days` property, which counts both the start and the end date (a block from Monday to Sunday lasts 7 days).

**Why:** Any one of the three can be calculated from the other two. Storing all three lets them drift apart, for example when a block is extended and only the end date is changed.

## 16. Only one active block per user

**Date:** 2026-11-05

**Decision:** A user can have many blocks, but only one of them can be active at a time. This is enforced in the database by a `UniqueConstraint` on `user` with `condition=Q(is_active=True)` (`training_block_one_active_per_user`). PostgreSQL builds it as a partial unique index that covers only active blocks, so any number of inactive blocks is allowed.

**Consequence:** switching the active block has to deactivate the old block before activating the new one, in a single transaction. In the opposite order, two blocks would be active for a moment and the constraint would reject the change.

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

## 18. Plan rules are enforced by database constraints

**Date:** 2026-11-06

**Decision:** The rules a training plan must follow are check and unique constraints in `Meta.constraints`, enforced by PostgreSQL:

- `TrainingBlock`: one active block per user (16), and `end_date >= start_date`, so `duration_days` cannot be negative. A one-day block (start equals end) is allowed.
- `PlannedDay` and `PlannedExercise`: `position` is unique within the parent block or day.
- `PlannedExercise`: `reps_max >= reps_min`, `sets > 0`, `reps_min > 0`, `rpe` between 0 and 10, `rir` at most 10, and `weight` between 0 and 1000 kg.

Constraint names start with the model name (for example `planned_exercise_reps_min_gt_0`), because they must be unique across the whole database.

**Alternative considered:** Validators on the model fields or in forms only.

**Why:** Validators run only when something calls `full_clean()`, which `save()`, `objects.create()`, the shell, and raw SQL do not do. A constraint holds whichever way the data arrives, including the future LLM-generated blocks. Optional fields (`rpe`, `rir`, `weight`) need no extra `NULL` handling, because a `CHECK` constraint rejects only a false result, and a comparison with `NULL` is unknown, not false.

**Consequence:** Adding a constraint fails if existing rows already break it. Locally the data was fixed by hand before `migrate`. On a production database, a data migration (`RunPython`) that cleans up existing rows has to run before the migration that adds the constraint.

**Tests:** Each constraint has a test that expects `IntegrityError` and a test for the boundary value that must still pass (for example `reps_min == reps_max`, `rpe` of 0 and 10, `rpe=None`).

## 19. Test data comes from factory fixtures

**Date:** 2026-11-06

**Decision:** The root `conftest.py` provides factory fixtures (`make_user`, `make_profile`, `make_exercise`, `make_block`, `make_day`, `make_planned_exercise`). Each returns a function that takes field overrides as keyword arguments, fills in valid defaults, and creates a missing parent object through the parent's factory. A shared `itertools.count` counter keeps unique fields (`username`, `email`, `Exercise.name`) from colliding.

**Alternative considered:** Fixtures that each return one ready-made object.

**Why:** Many tests need two objects of the same kind with different values, for example two blocks of the same user, one active and one not. A factory gives that with two calls, without a new fixture for every case. Defaults always satisfy every constraint, so an `IntegrityError` in a test means a real problem, not a collision in test data. Tests that check a rule "within a parent" (positions, the active block) create the parent explicitly and pass it to every call, because a factory called without it builds a new parent each time.

## 20. Blocks are ordered newest first

**Date:** 2026-11-06

**Decision:** `TrainingBlock` has `ordering = ["-start_date", "-id"]`.

**Why:** Blocks are a training history, and the current or latest block is the one most often needed. `-id` breaks ties between blocks with the same start date, so the order is fully deterministic. `ordering` changes only the `ORDER BY` of queries, not the table, so its migration (`AlterModelOptions`) runs no SQL.

## 21. Choice fields have room to grow

**Date:** 2026-11-06

**Decision:** `Exercise.category` and `Profile.goal` have `max_length=20`.

**Why:** The longest existing values (`horizontal_push`, `general_fitness`) were exactly 15 characters, the previous limit. Any longer choice added later would have failed only when saved. The extra room costs nothing in PostgreSQL, where `varchar(n)` stores only the actual length.

## 22. Email rules are enforced by database constraints

**Date:** 2026-11-09

**Context:** Creating a user in the admin with `TEST@EXAMPLE.COM`, while `test@example.com` existed, ended in a 500 error from PostgreSQL instead of a form error. The database had a case-insensitive unique index, but the model had no `Meta.constraints`, so Django never validated the rule. The index came from a migration that had been applied locally and then disappeared from the repository (only its `.pyc` cache was left), so the database and the code were out of sync. Because the local data was only test data, the database was reset (`docker compose down -v`) and the rules were written properly.

**Decision:** `User.Meta.constraints` has `user_email_ci_unique` (a `UniqueConstraint` on `Lower("email")`, with the message "A user with that email already exists.") and `user_email_not_empty` (a `CheckConstraint` with `~Q(email="")`). The email field no longer has `unique=True`. `User.Meta` extends `AbstractUser.Meta`, so the inherited options (`verbose_name`) are kept.

**Alternatives considered:**

- Keeping `unique=True` next to the new constraint: two indexes for one rule, and an exact duplicate would show two error messages.
- A raw `CREATE UNIQUE INDEX` in a migration: the database enforces it, but Django does not know about it and cannot show a form error. This was the original bug.

**Why:** A constraint in `Meta` is enforced by the database and also validated by Django in model forms, so bad data is rejected with a readable message before it reaches the database. Because a constraint built on an expression is not tied to one field, the duplicate error appears as a non-field error (`NON_FIELD_ERRORS`), at the top of the form.

**Consequence:** Claude Code may no longer create, edit or apply migrations (see `CLAUDE.md`). Applied migrations are never edited by hand; only formatting changes by `ruff format` are accepted.

## 23. The admin uses a subclass of Django's UserAdmin

**Date:** 2026-11-09

**Decision:** `accounts/admin.py` registers a subclass of `django.contrib.auth.admin.UserAdmin` and adds `email` to `add_fieldsets`, copied from the installed Django version (it includes `usable_password`). `list_display` and `search_fields` already contain `email` in the base class.

**Alternative considered:** A plain `ModelAdmin`: its form would save the password as plain text instead of hashing it.

**Tests:** `accounts/tests/test_admin.py` uses the `admin_client` fixture: the add form has an email field, a valid POST redirects to the new user's change page and stores a hashed password, and a case-insensitive duplicate or an empty email re-renders the form with an error and creates no user.

## 24. The exercise library is a fixture with fixed primary keys

**Date:** 2026-11-09

**Decision:** `training/fixtures/exercises.json` holds the exercises of the current training block, loaded with `loaddata exercises`. Every entry has an explicit `pk`, so loading again updates the same rows. An exercise variant gets its own entry when its loads are not comparable with the base exercise (leg press with feet low or high, seated leg curl with one or two legs, dumbbell or cable lateral raise). A heavier and a lighter prescription of the same movement (hip thrust) is one exercise; the difference belongs to `PlannedExercise`.

**Alternative considered:** A data migration (`RunPython`): right for data that must exist on every database, including production. The library is still being shaped, so a fixture is enough for now.

**Known limitation:** `loaddata` does not call `full_clean()`, so a wrong `category` value (a label instead of the stored value) would load without an error. Only database constraints apply.

## 25. The training plan admin has two levels of inlines

**Date:** 2026-11-09

**Decision:** `TrainingBlockAdmin` shows days as a `TabularInline` with `show_change_link`, and `PlannedDayAdmin` shows exercises as a `TabularInline` with `autocomplete_fields` for the exercise. Inlines have `extra = 0`. List views use `list_select_related` for the foreign keys they display, and `ProfileAdmin` uses it for `user`, because `Profile.__str__` reads `user.username`.

**Alternative considered:** Nested inlines (exercises inside days inside a block) through a third-party package: Django does not support them, and a dependency only for the admin is not worth it.

**How it was made:** The admin configuration was generated by Claude Code from a written specification, then reviewed line by line and tested by hand in the browser before committing.
