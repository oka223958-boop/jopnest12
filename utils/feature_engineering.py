"""
==============================================================
  utils/feature_engineering.py  —  Feature Engineering
==============================================================
  All feature computation logic lives here so that:
    • Training pipeline and API use IDENTICAL features.
    • No feature logic is duplicated across files.

  Key functions:
    build_features()     → add engineered columns to df
    build_text_corpus()  → combine text fields for TF-IDF
    user_profile_text()  → single text string for a user
    job_profile_text()   → single text string for a job
==============================================================
"""

import numpy as np
import pandas as pd

from utils.logger import get_logger

log = get_logger(__name__)


# ─────────────────────────────────────────────────────────────
#  PUBLIC INTERFACE
# ─────────────────────────────────────────────────────────────

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add / recompute all engineered feature columns on a DataFrame.
    Safe to call on both the full training set and a single-row
    inference DataFrame.

    Args:
        df: DataFrame that must have the raw user & job columns.

    Returns:
        df with new/updated feature columns appended.
    """
    log.info("Building engineered features...")

    df = df.copy()  # never mutate the caller's DataFrame

    # ── Parse salary strings → integers ──────────────────────
    df["user_salary_min"], df["user_salary_max"] = zip(
        *df["expected_salary_egp"].map(_parse_salary_range)
    )
    df["job_salary_min"], df["job_salary_max"] = zip(
        *df["salary_range_egp"].map(_parse_salary_range)
    )

    # ── Skill overlap ratio (0–1) ─────────────────────────────
    df["skill_match_score"] = df.apply(
        lambda r: _skill_match(r["user_skills"], r["job_required_skills"]),
        axis=1,
    )

    # ── Binary flag features ──────────────────────────────────
    df["location_match"] = (
        df["user_location"] == df["job_location"]
    ).astype(int)

    df["salary_fit"] = (
        (df["job_salary_min"] <= df["user_salary_max"]) &
        (df["job_salary_max"] >= df["user_salary_min"])
    ).astype(int)

    df["exp_required_min"] = df["experience_required"].map(_parse_exp_min)
    df["experience_fit"] = (
        df["experience_years"] >= df["exp_required_min"]
    ).astype(int)

    df["job_type_match"] = df.apply(
        lambda r: _job_type_match(r["preferred_job_type"], r["job_type"]),
        axis=1,
    )

    # ── Composite recommendation score (weighted sum) ─────────
    df["recommendation_score"] = _composite_score(df)

    # ── Binary target label ───────────────────────────────────
    df["is_good_match"] = (
        (df["applied"] == True) | (df["recommendation_score"] >= 5)
    ).astype(int)

    log.info("Feature engineering complete ✓")
    return df


def build_text_corpus(
    df: pd.DataFrame,
    user_fields: list,
    job_fields: list,
) -> list[str]:
    """
    Combine user and job text columns into a single string per row.
    Used to fit/transform the TF-IDF vectorizer.

    Args:
        df          : Full interactions DataFrame.
        user_fields : List of user-side text column names.
        job_fields  : List of job-side text column names.

    Returns:
        List of combined text strings (one per row).
    """
    all_fields = user_fields + job_fields
    corpus = (
        df[all_fields]
        .fillna("")
        .apply(lambda row: " ".join(row.astype(str)), axis=1)
        .str.lower()
        .str.replace(r"[|,]", " ", regex=True)  # normalize delimiters
        .tolist()
    )
    log.info(f"Text corpus built: {len(corpus):,} documents")
    return corpus


def user_profile_text(user: pd.Series) -> str:
    """
    Combine a user record into a single searchable text string.

    Args:
        user: A single-row Series from the users table.

    Returns:
        Cleaned combined text for TF-IDF lookup.
    """
    parts = [
        str(user.get("user_skills", "")),
        str(user.get("cv_summary", "")),
    ]
    return _clean_text(" ".join(parts))


def job_profile_text(job: pd.Series) -> str:
    """
    Combine a job record into a single searchable text string.

    Args:
        job: A single-row Series from the jobs table.

    Returns:
        Cleaned combined text for TF-IDF lookup.
    """
    parts = [
        str(job.get("job_required_skills", "")),
        str(job.get("title", "")),
        str(job.get("job_description", "")),
    ]
    return _clean_text(" ".join(parts))


# ─────────────────────────────────────────────────────────────
#  PRIVATE HELPERS
# ─────────────────────────────────────────────────────────────

def _parse_salary_range(salary_str: str) -> tuple[int, int]:
    """
    Parse '5000-8000' → (5000, 8000).
    Returns (0, 0) if parsing fails.
    """
    try:
        parts = str(salary_str).split("-")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return 0, 0


def _parse_exp_min(exp_str: str) -> int:
    """
    Parse '2-5' → 2  (minimum years required).
    Returns 0 if parsing fails.
    """
    try:
        return int(str(exp_str).split("-")[0])
    except (ValueError, IndexError):
        return 0


def _skill_match(user_skills: str, job_skills: str) -> float:
    """
    Jaccard-like skill overlap ratio.
    = |user_skills ∩ job_skills| / |job_skills|

    Returns 0.0 if either side is empty or NaN.
    """
    if pd.isna(user_skills) or pd.isna(job_skills):
        return 0.0
    user_set = set(str(user_skills).lower().split("|"))
    job_set  = set(str(job_skills).lower().split("|"))
    if not job_set:
        return 0.0
    return round(len(user_set & job_set) / len(job_set), 4)


def _job_type_match(preferred: str, job_type: str) -> int:
    """
    Return 1 if job_type is in the user's preferred types, else 0.
    preferred example: 'Remote|Part Time|Internship'
    """
    if pd.isna(preferred) or pd.isna(job_type):
        return 0
    pref_set = set(str(preferred).lower().split("|"))
    return int(str(job_type).lower() in pref_set)


def _composite_score(df: pd.DataFrame) -> pd.Series:
    """
    Weighted composite recommendation score (rough range 0–10).
    Weights were tuned based on domain knowledge of job matching.
    """
    return (
        df["interaction_score"]  * 0.25 +
        df["skill_match_score"]  * 3.00 +   # most impactful
        df["location_match"]     * 1.00 +
        df["salary_fit"]         * 1.50 +
        df["experience_fit"]     * 1.00 +
        df["job_type_match"]     * 1.00 +
        df["user_rating"].fillna(3) * 0.50
    ).round(4)


def _clean_text(text: str) -> str:
    """Lowercase and normalize pipe/comma delimiters to spaces."""
    return (
        text.lower()
        .replace("|", " ")
        .replace(",", " ")
        .strip()
    )
