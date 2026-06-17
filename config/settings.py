"""
==============================================================
  JobNest - Configuration & Settings
==============================================================
  Central config file for all project constants and paths.
  Any change to paths or hyperparameters happens HERE only.
==============================================================
"""

import os

# ─────────────────────────────────────────────
#  ROOT PATHS
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # config/
BASE_DIR = os.path.dirname(BASE_DIR)                            # jobnest/
DATA_DIR   = os.path.join(BASE_DIR, "data")
MODEL_DIR  = os.path.join(BASE_DIR, "models", "saved")
LOG_DIR    = os.path.join(BASE_DIR, "logs")

# ─────────────────────────────────────────────
#  DATA FILE NAMES
# ─────────────────────────────────────────────
RAW_DATA_FILE      = "jobnest_enhanced_dataset.csv"
JOBS_CACHE_FILE    = "jobs_cache.pkl"      # deduplicated jobs table
USERS_CACHE_FILE   = "users_cache.pkl"     # deduplicated users table

# ─────────────────────────────────────────────
#  FEATURE COLUMNS (used across modules)
# ─────────────────────────────────────────────

# Numeric features fed to ML model
NUMERIC_FEATURES = [
    "skill_match_score",
    "location_match",
    "salary_fit",
    "experience_fit",
    "job_type_match",
    "interaction_score",
    "experience_years",
]

# Text fields combined for TF-IDF content similarity
USER_TEXT_FIELDS = ["user_skills", "cv_summary"]
JOB_TEXT_FIELDS  = ["job_required_skills", "title", "job_description"]

# Target label for supervised model
TARGET_COLUMN = "is_good_match"

# ─────────────────────────────────────────────
#  TF-IDF SETTINGS
# ─────────────────────────────────────────────
TFIDF_MAX_FEATURES  = 5000    # vocabulary size
TFIDF_NGRAM_RANGE   = (1, 2)  # unigrams + bigrams
TFIDF_MIN_DF        = 2       # ignore very rare terms

# ─────────────────────────────────────────────
#  ML MODEL HYPERPARAMETERS
# ─────────────────────────────────────────────
RANDOM_FOREST_PARAMS = {
    "n_estimators"  : 300,
    "max_depth"     : 15,
    "min_samples_split": 5,
    "class_weight"  : "balanced",   # handles label imbalance automatically
    "random_state"  : 42,
    "n_jobs"        : -1,           # use all CPU cores
}

GRADIENT_BOOST_PARAMS = {
    "n_estimators"  : 200,
    "learning_rate" : 0.05,
    "max_depth"     : 6,
    "subsample"     : 0.8,
    "random_state"  : 42,
}

# ─────────────────────────────────────────────
#  RECOMMENDATION SETTINGS
# ─────────────────────────────────────────────
TOP_N_RECOMMENDATIONS = 10    # default number of jobs to return
CONTENT_WEIGHT        = 0.4   # weight of TF-IDF cosine score in hybrid
ML_WEIGHT             = 0.6   # weight of ML model score in hybrid

# ─────────────────────────────────────────────
#  FLASK API SETTINGS
# ─────────────────────────────────────────────
API_HOST  = "0.0.0.0"
API_PORT  = 5000
API_DEBUG = True    # set False in production

# ─────────────────────────────────────────────
#  ENSURE DIRECTORIES EXIST AT IMPORT TIME
# ─────────────────────────────────────────────
for _dir in [DATA_DIR, MODEL_DIR, LOG_DIR]:
    os.makedirs(_dir, exist_ok=True)
