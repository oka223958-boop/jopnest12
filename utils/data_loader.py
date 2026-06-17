"""
==============================================================
  utils/data_loader.py  —  Data Loading & Caching
==============================================================
  Responsibilities:
    1. Load the main CSV dataset.
    2. Build & cache a deduplicated JOBS table.
    3. Build & cache a deduplicated USERS table.
    4. Provide a clean API so models never touch file paths.

  All heavy I/O happens ONCE then is served from pickle cache.
==============================================================
"""

import os
import pickle

import pandas as pd

from config.settings import (
    DATA_DIR,
    RAW_DATA_FILE,
    JOBS_CACHE_FILE,
    USERS_CACHE_FILE,
)
from utils.logger import get_logger

log = get_logger(__name__)


# ─────────────────────────────────────────────────────────────
#  PUBLIC INTERFACE  (call these from other modules)
# ─────────────────────────────────────────────────────────────

def load_dataset() -> pd.DataFrame:
    """
    Load the full interaction dataset from CSV.

    Returns:
        df (DataFrame): 120 000-row interactions table.

    Raises:
        FileNotFoundError: If the CSV file is missing.
    """
    path = os.path.join(DATA_DIR, RAW_DATA_FILE)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset not found at: {path}\n"
            f"Please copy jobnest_enhanced_dataset.csv into the data/ folder."
        )

    log.info(f"Loading dataset from {path} ...")
    df = pd.read_csv(path, low_memory=False, dtype={"experience_required": str})
    df["experience_required"] = df["experience_required"].apply(_fix_experience)
    df = pd.read_csv(path, low_memory=False)

    # ── Basic validation ──────────────────────────────────────
    _validate_columns(df)

    log.info(f"Dataset loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


def load_jobs(df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Return a deduplicated jobs table (one row per job_id).
    Builds from df if not cached, else loads pickle.

    Args:
        df: Full interactions DataFrame (optional if cache exists).

    Returns:
        jobs (DataFrame): ~2 000 unique job records.
    """
    cache_path = os.path.join(DATA_DIR, JOBS_CACHE_FILE)

    # Serve from cache if available
    if os.path.exists(cache_path):
        log.info("Loading jobs from cache...")
        return _load_pickle(cache_path)

    # Build fresh from the full dataset
    if df is None:
        df = load_dataset()

    log.info("Building jobs cache...")
    jobs = _build_jobs_table(df)

    _save_pickle(jobs, cache_path)
    log.info(f"Jobs table built: {len(jobs):,} unique jobs → cached")
    return jobs


def load_users(df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Return a deduplicated users table (one row per user_id).
    Builds from df if not cached, else loads pickle.

    Args:
        df: Full interactions DataFrame (optional if cache exists).

    Returns:
        users (DataFrame): ~9 000 unique user records.
    """
    cache_path = os.path.join(DATA_DIR, USERS_CACHE_FILE)

    if os.path.exists(cache_path):
        log.info("Loading users from cache...")
        return _load_pickle(cache_path)

    if df is None:
        df = load_dataset()

    log.info("Building users cache...")
    users = _build_users_table(df)

    _save_pickle(users, cache_path)
    log.info(f"Users table built: {len(users):,} unique users → cached")
    return users


# ─────────────────────────────────────────────────────────────
#  PRIVATE HELPERS  (not imported outside this module)
# ─────────────────────────────────────────────────────────────

def _validate_columns(df: pd.DataFrame) -> None:
    """Check that critical columns are present; raise if missing."""
    required = [
        "user_id", "job_id", "user_skills", "job_required_skills",
        "skill_match_score", "is_good_match",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in dataset: {missing}")
    log.info("Column validation passed ✓")


def _build_jobs_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract all job-side columns, drop duplicates, reset index.
    """
    job_cols = [
        "job_id", "title", "job_required_skills", "job_type",
        "job_location", "location_scope", "company_name",
        "job_description", "salary_range_egp", "experience_required",
        "company_size", "industry", "job_salary_min", "job_salary_max",
    ]
    return (
        df[job_cols]
        .drop_duplicates(subset="job_id")
        .reset_index(drop=True)
    )


def _build_users_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract all user-side columns, keep most-recent record per user.
    """
    user_cols = [
        "user_id", "user_name", "role", "user_skills", "user_location",
        "experience_years", "education", "expected_salary_egp",
        "preferred_job_type", "cv_summary",
        "user_salary_min", "user_salary_max",
    ]
    return (
        df[user_cols]
        .drop_duplicates(subset="user_id")
        .reset_index(drop=True)
    )


<<<<<<< HEAD
_MONTH_MAP = {
    "Jan": "1", "Feb": "2", "Mar": "3", "Apr": "4",
    "May": "5", "Jun": "6", "Jul": "7", "Aug": "8",
    "Sep": "9", "Oct": "10", "Nov": "11", "Dec": "12",
}

def _fix_experience(val: str) -> str:
    """Convert pandas date-corrupted values back to year ranges.
    e.g. '5-Feb' (Feb 5th) → '2-5', '7-Mar' (Mar 7th) → '3-7'
    """
    if not isinstance(val, str):
        return str(val)
    parts = val.split("-")
    if len(parts) == 2 and parts[1] in _MONTH_MAP:
        return f"{_MONTH_MAP[parts[1]]}-{parts[0]}"
    return val


=======
>>>>>>> 232f31a7c90ab4e785257eec9cb8d78e80333078
def _save_pickle(obj, path: str) -> None:
    """Serialize an object to disk with pickle."""
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def _load_pickle(path: str):
    """Deserialize an object from a pickle file."""
    with open(path, "rb") as f:
        return pickle.load(f)
