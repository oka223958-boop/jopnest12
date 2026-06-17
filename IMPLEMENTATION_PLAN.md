# JobNest — Dynamic Ingestion Implementation Plan

> **Goal:** Allow new jobs, companies, users, and courses to be added to the system via API endpoints,
> ensuring they are indexed for recommendations immediately and persisted to disk
> to survive server restarts.

---

## Overview

This project has evolved from static CSV-based loading to a dynamic pipeline. 
Data is now managed in live DataFrames with disk-based persistence (pickle caches).

1.  **Accepted and validated** via Pydantic schemas.
2.  **Added to live in-memory pool** (Pandas DataFrames).
3.  **Indexed for search/recommendation** (TF-IDF matrix updates for jobs).
4.  **Persisted to disk** (`.pkl` cache files) for durability.
5.  **Instantly rankable** by the recommendation engines.

---

## Step-by-Step Plan

### ✅ Step 1 — POST /api/jobs/new Endpoint
**Status:** ✅ DONE

- Added `NewJobRequest` Pydantic model.
- Added `POST /api/jobs/new` endpoint to `api/routes.py`.

---

### ✅ Step 2 — Update TF-IDF Matrix Incrementally
**Status:** ✅ DONE

- Added `add_job()` method to `ContentBasedRecommender`.
- Wired incremental matrix updates into the Job ingestion endpoint.

---

### ✅ Step 3 — Disk Persistence (Jobs)
**Status:** ✅ DONE

- Created `utils/persistence.py` for pickle serialization.
- Updated `app.py` to prefer `jobs_cache.pkl` on startup.

---

### ✅ Step 4 — Background ML Scoring
**Status:** ✅ DONE

- Integrated FastAPI `BackgroundTasks` for non-blocking ML scoring.

---

### ✅ Step 5 — Verification Endpoint
**Status:** ✅ DONE

- Added `GET /api/jobs/{job_id}/score` to verify indexing.

---

### ✅ Step 6 — Dynamic User Ingestion
**Status:** ✅ DONE
**Files:** `api/routes.py`, `utils/persistence.py`, `app.py`

-   **Schema**: Add `NewUserRequest` Pydantic model:
    -   `user_name`, `user_skills`, `role`, `user_location`, `experience_years`, `preferred_job_type`, `expected_salary_egp`.
-   **Endpoint**: Add `POST /api/users/new`:
    -   Auto-assign `user_id = max(existing) + 1`.
    -   Append to live `_users` DataFrame.
    -   Call persistence to save updated user pool.
-   **Persistence**: 
    -   Add `save_users(users)` to `utils/persistence.py`.
    -   Add `load_users_from_cache()` to `utils/persistence.py`.
-   **Restoration**: Update `app.py` lifespan to load users from cache if available.

---

### ✅ Step 7 — Dynamic Course Ingestion
**Status:** ✅ DONE
**Files:** `api/routes.py`, `utils/persistence.py`, `app.py`

-   **Schema**: Add `NewCourseRequest` Pydantic model:
    -   `title`, `specialty`, `platform`, `level`, `language`, `price`, `rating`, `skills`.
-   **Endpoint**: Add `POST /api/courses/new`:
    -   Auto-assign `course_id = max(existing) + 1`.
    -   Append to live `_courses` DataFrame.
    -   Call persistence.
-   **Persistence**: 
    -   Add `save_courses(courses)` and `load_courses_from_cache()`.
-   **Restoration**: Update `app.py` lifespan to load courses from cache.

---

## Files Modified / Created

| File | Action |
|------|--------|
| `api/routes.py` | Added Ingestion Endpoints (Jobs, Users, Courses) |
| `models/content_model.py` | Incremental TF-IDF support |
| `app.py` | Cache-first startup logic |
| `utils/persistence.py` | Multi-table pickle persistence |
| `IMPLEMENTATION_PLAN.md` | This file |
| `PROGRESS_LOG.md` | Completed steps log |
