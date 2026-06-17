# JobNest — Progress Log

> Brief record of every completed implementation step.
> Full details are in `IMPLEMENTATION_PLAN.md`.

---

## ✅ Step 1 — POST /api/jobs/new Endpoint
**Date:** 2026-04-28
**File changed:** `api/routes.py`

- Added `NewJobRequest` Pydantic model with 9 fields (3 required, 6 with defaults).
- Added `POST /api/jobs/new` endpoint:
  - Validates incoming JSON automatically via Pydantic.
  - Auto-assigns `job_id = max(existing_ids) + 1`.
  - Fills missing DataFrame columns with empty strings.
  - Appends the new row to the live `_jobs` DataFrame.
  - Returns `202 Accepted` with `{ status, job_id, message }`.
- Changed `from typing import Optional` → `from typing import List, Optional`.

---

## ✅ Step 2 — Incremental TF-IDF Matrix Update
**Date:** 2026-04-28
**Files changed:** `models/content_model.py`, `api/routes.py`

- Added `import scipy.sparse` to `content_model.py`.
- Added `add_job(job_row: pd.Series)` method to `ContentBasedRecommender`:
  - Calls `job_profile_text(job_row)` to build text.
  - Uses the **frozen** fitted vectorizer (`.transform()`, not `.fit_transform()`).
  - Stacks the new sparse vector onto `self.job_matrix` via `scipy.sparse.vstack()`.
  - Appends the row to `self.jobs_ref` to keep matrix ↔ DataFrame indices aligned.
- Updated `POST /api/jobs/new` in `routes.py` to call `_engine.content_model.add_job()`
  immediately after the DataFrame append.
- New jobs are now **visible to the recommendation engine on the next request**
  without any retraining.

---

## ✅ Step 3 — Disk Persistence
**Date:** 2026-04-28
**Files changed:** `utils/persistence.py` (new), `api/routes.py`, `app.py`

- Created `utils/persistence.py` with three functions:
  - `save_jobs(jobs)` → serializes `_jobs` DataFrame to `data/jobs_cache.pkl`
  - `save_tfidf(content_model)` → saves updated `tfidf_job_matrix.pkl` + `tfidf_jobs_ref.pkl`
  - `save_all(jobs, content_model)` → convenience wrapper calling both above
  - `load_jobs_from_cache()` → loads from cache if it exists, returns `None` on first run
- Updated `api/routes.py`:
  - Imported `save_all` from `utils.persistence`
  - Called `save_all(_jobs, _engine.content_model)` at the end of `POST /api/jobs/new`
  - Wrapped in `try/except` so a disk error never crashes the response
- Updated `app.py` lifespan:
  - Imported `load_jobs_from_cache`
  - On startup: tries `jobs_cache.pkl` first; falls back to raw CSV if not found
  - Added log messages to distinguish cache vs CSV loading

---

## ✅ Step 4 — Background ML Scoring
**Date:** 2026-04-30
**File changed:** `api/routes.py`

- Added `BackgroundTasks` to `add_new_job` endpoint.
- Implemented `_rank_new_job_background` function to handle async scoring.
- Documented that actual pre-computation isn't strictly necessary for the current architecture since the `recommend()` endpoint scores the top 50 candidates on the fly based on the updated TF-IDF matrix.

---

## ✅ Step 5 — Verification Endpoint
**Date:** 2026-04-30
**File changed:** `api/routes.py`

- Added `GET /api/jobs/{job_id}/score` endpoint.
- Endpoint verifies if the job exists in the live `_jobs` DataFrame.
- Endpoint verifies if the job has been successfully appended to the TF-IDF matrix (`jobs_ref`).
- Returns a JSON response with status and current matrix size.

---

## ✅ Step 6 — Dynamic User Ingestion
**Date:** 2026-04-30
**Files changed:** `api/routes.py`, `app.py`

- Added `NewUserRequest` Pydantic model with the required user fields.
- Added `POST /api/users/new` endpoint:
  - Validates incoming JSON via Pydantic.
  - Auto-assigns `user_id = max(existing_ids) + 1`.
  - Fills missing DataFrame columns with empty strings.
  - Appends the new row to the live `_users` DataFrame.
  - Persists updated users to `data/users_cache.pkl` via `save_users()`.
  - Keeps `ChatbotEngine` synchronized by updating `_chatbot.users`.
- Updated `app.py` lifespan to prefer `users_cache.pkl` on startup, falling back to CSV on first run.

---

## ✅ Step 7 — Dynamic Course Ingestion
**Date:** 2026-04-30
**Files changed:** `api/routes.py`, `utils/persistence.py`, `app.py`

- Added `NewCourseRequest` Pydantic model aligned to the existing courses dataset fields.
- Added `POST /api/courses/new` endpoint:
  - Auto-assigns `course_id = max(existing_ids) + 1`.
  - Appends the new row to the live `_courses` DataFrame.
  - Persists updated courses to `data/courses_cache.pkl` via `save_courses()`.
  - Keeps `ChatbotEngine` synchronized by updating `_chatbot.courses`.
- Updated `utils/persistence.py` with `save_courses()` and `load_courses_from_cache()`.
- Updated `app.py` lifespan to prefer `courses_cache.pkl` on startup, falling back to CSV if not present.
