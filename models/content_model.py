"""
==============================================================
  models/content_model.py  —  TF-IDF Content-Based Filtering
==============================================================
  How it works:
    1. Each job is represented as a TF-IDF vector built from
       its required skills + title + description.
    2. A user is also represented as a TF-IDF vector built from
       their skills + CV summary.
    3. Cosine similarity between the user vector and ALL job
       vectors gives a relevance score (0–1) for every job.
    4. Top-N jobs by cosine score are returned.

  Why TF-IDF?
    • Fast, interpretable, no GPU needed.
    • "Python|Django" in user skills boosts jobs that mention
       those exact terms heavily.
    • Bigrams (ngram_range=(1,2)) catch "machine learning",
       "data analysis", etc. as single features.

  File is kept small: only TF-IDF logic lives here.
  All feature-building is delegated to utils/feature_engineering.
==============================================================
"""

import os
import pickle

import numpy as np
import pandas as pd
import scipy.sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config.settings import (
    MODEL_DIR,
    TFIDF_MAX_FEATURES,
    TFIDF_NGRAM_RANGE,
    TFIDF_MIN_DF,
    TOP_N_RECOMMENDATIONS,
)
from utils.logger import get_logger
from utils.feature_engineering import user_profile_text, job_profile_text

log = get_logger(__name__)

# Saved model file names
_VECTORIZER_FILE = os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")
_JOB_MATRIX_FILE = os.path.join(MODEL_DIR, "tfidf_job_matrix.pkl")
_JOBS_FILE       = os.path.join(MODEL_DIR, "tfidf_jobs_ref.pkl")


# ─────────────────────────────────────────────────────────────
#  PUBLIC CLASS
# ─────────────────────────────────────────────────────────────

class ContentBasedRecommender:
    """
    TF-IDF content-based job recommender.

    Example:
        recommender = ContentBasedRecommender()
        recommender.fit(jobs_df)
        top_jobs = recommender.recommend(user_series, top_n=10)
    """

    def __init__(self):
        # Vectorizer transforms text → TF-IDF sparse matrix
        self.vectorizer: TfidfVectorizer = TfidfVectorizer(
            max_features = TFIDF_MAX_FEATURES,
            ngram_range  = TFIDF_NGRAM_RANGE,
            min_df       = TFIDF_MIN_DF,
            sublinear_tf = True,  # log(1+tf) reduces impact of very frequent terms
        )
        self.job_matrix = None   # shape: (n_jobs, n_features)
        self.jobs_ref   = None   # reference to jobs DataFrame

        log.info("ContentBasedRecommender initialized")

    # ──────────────────────────────────────────────────────────
    #  FIT
    # ──────────────────────────────────────────────────────────

    def fit(self, jobs: pd.DataFrame) -> "ContentBasedRecommender":
        """
        Build TF-IDF matrix from all jobs.
        Call this ONCE during training; save() to persist.

        Args:
            jobs: Deduplicated jobs DataFrame from load_jobs().

        Returns:
            self (for chaining)
        """
        log.info(f"Fitting TF-IDF on {len(jobs):,} jobs...")

        # Build one text string per job  (skills + title + description)
        job_texts = jobs.apply(job_profile_text, axis=1).tolist()

        # Fit vectorizer + transform all jobs in one call
        self.job_matrix = self.vectorizer.fit_transform(job_texts)
        self.jobs_ref   = jobs.reset_index(drop=True)

        log.info(
            f"TF-IDF matrix: {self.job_matrix.shape} | "
            f"vocabulary size: {len(self.vectorizer.vocabulary_):,}"
        )
        return self

    # ──────────────────────────────────────────────────────────
    #  RECOMMEND
    # ──────────────────────────────────────────────────────────

    def recommend(
        self,
        user: pd.Series,
        top_n: int = TOP_N_RECOMMENDATIONS,
    ) -> pd.DataFrame:
        """
        Return top-N jobs for a user based on cosine similarity.

        Args:
            user  : Single-row Series from the users table.
            top_n : Number of jobs to return.

        Returns:
            DataFrame with job columns + 'content_score' (0–1).
        """
        self._assert_fitted()

        # Transform user profile into TF-IDF space
        user_text   = user_profile_text(user)
        user_vector = self.vectorizer.transform([user_text])  # sparse (1, n_features)

        # Cosine similarity: user vector vs every job vector
        # Result shape: (1, n_jobs)  →  flatten to 1-D array
        scores = cosine_similarity(user_vector, self.job_matrix).flatten()

        # Pick top-N indices (unsorted descending)
        top_indices = np.argpartition(scores, -top_n)[-top_n:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

        # Build result DataFrame
        result = self.jobs_ref.iloc[top_indices].copy()
        result["content_score"] = np.round(scores[top_indices], 4)

        log.debug(
            f"Content recommendations for user_id={user.get('user_id', '?')}: "
            f"top score={result['content_score'].iloc[0]:.4f}"
        )
        return result

    # ──────────────────────────────────────────────────────────
    #  INCREMENTAL UPDATE
    # ──────────────────────────────────────────────────────────

    def add_job(self, job_row: pd.Series) -> None:
        """
        Add a single new job to the live TF-IDF matrix WITHOUT retraining.

        Process:
          1. Build the job's text profile (same function used during fit).
          2. Transform it using the EXISTING fitted vectorizer  →  (1, n_features).
          3. Stack it onto the bottom of job_matrix using scipy.sparse.vstack.
          4. Append the row to jobs_ref so indices stay aligned.

        Note: The vocabulary is frozen at training time. New words in the
        job description that weren't in the original corpus are silently ignored.
        This is acceptable for most real-world job additions.

        Args:
            job_row: A pandas Series representing one job (same columns as jobs_ref).
        """
        self._assert_fitted()

        # Step 1 — Build text from the new job
        job_text   = job_profile_text(job_row)

        # Step 2 — Transform using the frozen vectorizer (no re-fit)
        new_vector = self.vectorizer.transform([job_text])   # shape: (1, n_features)

        # Step 3 — Append sparse vector to the matrix
        self.job_matrix = scipy.sparse.vstack([self.job_matrix, new_vector])

        # Step 4 — Append the row to jobs_ref (keep index aligned with matrix rows)
        new_df        = pd.DataFrame([job_row])
        self.jobs_ref = pd.concat([self.jobs_ref, new_df], ignore_index=True)

        log.info(
            f"ContentBasedRecommender: added job_id={job_row.get('job_id','?')} "
            f"| matrix now has {self.job_matrix.shape[0]:,} jobs"
        )

    # ──────────────────────────────────────────────────────────
    #  SAVE / LOAD
    # ──────────────────────────────────────────────────────────

    def save(self) -> None:
        """Persist vectorizer + job matrix + jobs reference to disk."""
        self._assert_fitted()
        _dump(self.vectorizer,  _VECTORIZER_FILE)
        _dump(self.job_matrix,  _JOB_MATRIX_FILE)
        _dump(self.jobs_ref,    _JOBS_FILE)
        log.info("ContentBasedRecommender saved ✓")

    def load(self) -> "ContentBasedRecommender":
        """
        Load a previously saved recommender from disk.
        Call this instead of fit() when the model already exists.
        """
        self.vectorizer  = _load(_VECTORIZER_FILE)
        self.job_matrix  = _load(_JOB_MATRIX_FILE)
        self.jobs_ref    = _load(_JOBS_FILE)
        log.info("ContentBasedRecommender loaded from disk ✓")
        return self

    def is_saved(self) -> bool:
        """Return True if all model files exist on disk."""
        return all(os.path.exists(f) for f in [
            _VECTORIZER_FILE, _JOB_MATRIX_FILE, _JOBS_FILE
        ])

    # ──────────────────────────────────────────────────────────
    #  PRIVATE
    # ──────────────────────────────────────────────────────────

    def _assert_fitted(self) -> None:
        """Raise if model has not been fit/loaded yet."""
        if self.job_matrix is None:
            raise RuntimeError(
                "ContentBasedRecommender is not fitted. "
                "Call fit() or load() first."
            )


# ─────────────────────────────────────────────────────────────
#  PICKLE HELPERS
# ─────────────────────────────────────────────────────────────

def _dump(obj, path: str) -> None:
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def _load(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)
