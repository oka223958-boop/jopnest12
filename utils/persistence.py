"""
==============================================================
  utils/persistence.py  —  Save / Load helpers for live data
==============================================================
  Called every time a new job is added via POST /api/jobs/new.

  Saves:
    1. data/jobs_cache.pkl          → updated _jobs DataFrame
    2. models/saved/tfidf_job_matrix.pkl  → updated sparse matrix
    3. models/saved/tfidf_jobs_ref.pkl    → updated jobs_ref DataFrame

  On startup (app.py lifespan), jobs_cache.pkl is preferred over
  the raw CSV so previously added jobs are automatically restored.
==============================================================
"""

import os
import pickle

import pandas as pd

from utils.logger import get_logger

log = get_logger(__name__)

# ── Paths ──────────────────────────────────────────────────────
_BASE_DIR       = os.path.dirname(os.path.dirname(__file__))
_JOBS_CACHE     = os.path.join(_BASE_DIR, "data",   "jobs_cache.pkl")
_USERS_CACHE    = os.path.join(_BASE_DIR, "data",   "users_cache.pkl")
_COURSES_CACHE  = os.path.join(_BASE_DIR, "data",   "courses_cache.pkl")
_MATRIX_FILE    = os.path.join(_BASE_DIR, "models", "saved", "tfidf_job_matrix.pkl")
_JOBS_REF_FILE  = os.path.join(_BASE_DIR, "models", "saved", "tfidf_jobs_ref.pkl")


# ──────────────────────────────────────────────────────────────
#  SAVE
# ──────────────────────────────────────────────────────────────

def save_jobs(jobs: pd.DataFrame) -> None:
    """
    Serialize the live _jobs DataFrame to disk.
    Called after every successful POST /api/jobs/new.
    """
    try:
        with open(_JOBS_CACHE, "wb") as f:
            pickle.dump(jobs, f)
        log.info(f"jobs_cache.pkl saved ({len(jobs):,} jobs)")
    except Exception as e:
        log.warning(f"Could not save jobs_cache.pkl: {e}")


def save_users(users: pd.DataFrame) -> None:
    """
    Serialize the live _users DataFrame to disk.
    Called after every successful POST /api/users/new.
    """
    try:
        with open(_USERS_CACHE, "wb") as f:
            pickle.dump(users, f)
        log.info(f"users_cache.pkl saved ({len(users):,} users)")
    except Exception as e:
        log.warning(f"Could not save users_cache.pkl: {e}")


def save_courses(courses: pd.DataFrame) -> None:
    """
    Serialize the live _courses DataFrame to disk.
    Called after every successful POST /api/courses/new.
    """
    try:
        with open(_COURSES_CACHE, "wb") as f:
            pickle.dump(courses, f)
        log.info(f"courses_cache.pkl saved ({len(courses):,} courses)")
    except Exception as e:
        log.warning(f"Could not save courses_cache.pkl: {e}")


def save_tfidf(content_model) -> None:
    """
    Serialize the updated TF-IDF matrix and jobs_ref to disk.
    Keeps the saved model files in sync with the live in-memory state.

    Args:
        content_model: A fitted ContentBasedRecommender instance.
    """
    try:
        with open(_MATRIX_FILE, "wb") as f:
            pickle.dump(content_model.job_matrix, f)
        with open(_JOBS_REF_FILE, "wb") as f:
            pickle.dump(content_model.jobs_ref, f)
        log.info(
            f"TF-IDF matrix saved "
            f"({content_model.job_matrix.shape[0]:,} jobs × "
            f"{content_model.job_matrix.shape[1]:,} features)"
        )
    except Exception as e:
        log.warning(f"Could not save TF-IDF files: {e}")


def save_all(jobs: pd.DataFrame, content_model) -> None:
    """
    Convenience wrapper — saves both jobs cache and TF-IDF files.
    This is the single call made from routes.py after adding a job.
    """
    save_jobs(jobs)
    save_tfidf(content_model)


# ──────────────────────────────────────────────────────────────
#  LOAD
# ──────────────────────────────────────────────────────────────

def load_jobs_from_cache() -> pd.DataFrame | None:
    """
    Load jobs from the pickle cache if it exists.
    Returns None if no cache file is present (first run).

    Usage in app.py lifespan:
        cached = load_jobs_from_cache()
        jobs   = cached if cached is not None else load_jobs(df)
    """
    if not os.path.exists(_JOBS_CACHE):
        log.info("No jobs_cache.pkl found — will load from CSV")
        return None
    try:
        with open(_JOBS_CACHE, "rb") as f:
            jobs = pickle.load(f)
        log.info(f"Loaded jobs from cache: {len(jobs):,} jobs")
        return jobs
    except Exception as e:
        log.warning(f"Could not load jobs_cache.pkl ({e}) — falling back to CSV")
        return None


def load_users_from_cache() -> pd.DataFrame | None:
    """
    Load users from the pickle cache if it exists.
    """
    if not os.path.exists(_USERS_CACHE):
        return None
    try:
        with open(_USERS_CACHE, "rb") as f:
            users = pickle.load(f)
        log.info(f"Loaded users from cache: {len(users):,} users")
        return users
    except Exception as e:
        log.warning(f"Could not load users_cache.pkl ({e}) — falling back to CSV")
        return None


def load_courses_from_cache() -> pd.DataFrame | None:
    """
    Load courses from the pickle cache if it exists.
    """
    if not os.path.exists(_COURSES_CACHE):
        return None
    try:
        with open(_COURSES_CACHE, "rb") as f:
            courses = pickle.load(f)
        log.info(f"Loaded courses from cache: {len(courses):,} courses")
        return courses
    except Exception as e:
        log.warning(f"Could not load courses_cache.pkl ({e}) — falling back to CSV")
        return None
