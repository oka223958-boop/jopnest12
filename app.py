"""
==============================================================
  app.py  —  FastAPI Application Entry Point
==============================================================
  Run:
      uvicorn app:app --reload --host 0.0.0.0 --port 8000

  Swagger UI (test from browser):
      http://127.0.0.1:8000/docs
==============================================================
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router, init_routes
from models.hybrid_engine import HybridRecommendationEngine
from utils.data_loader import load_dataset, load_jobs, load_users
from utils.persistence import load_jobs_from_cache, load_users_from_cache, load_courses_from_cache
from utils.logger import get_logger

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models and data ONCE when the server starts."""
    log.info("Loading recommendation engine...")
    engine = HybridRecommendationEngine()

    if engine.is_ready():
        engine.load()
        log.info("Models loaded from disk")
    else:
        log.warning("Models not found — run python train.py first!")

    log.info("Loading data tables...")
    df    = load_dataset()
    users = load_users_from_cache()
    if users is None:
        users = load_users(df)
        log.info(f"Users loaded from CSV: {len(users):,} rows")
    else:
        log.info(f"Users loaded from cache: {len(users):,} rows (includes added users)")

    # ── Prefer jobs cache (includes previously added jobs) ────
    # If jobs_cache.pkl exists, load from it.
    # Otherwise fall back to the raw CSV (first run).
    jobs = load_jobs_from_cache()
    if jobs is None:
        jobs = load_jobs(df)
        log.info(f"Jobs loaded from CSV: {len(jobs):,} rows")
    else:
        log.info(f"Jobs loaded from cache: {len(jobs):,} rows (includes added jobs)")

    # ── Prefer courses cache (includes previously added courses) ─
    courses = load_courses_from_cache()
    if courses is not None:
        log.info(f"Courses loaded from cache: {len(courses):,} rows (includes added courses)")
    else:
        courses = None
    try:
        import pandas as _pd, os as _os
        courses_path = _os.path.join(_os.path.dirname(__file__), "data", "jobnest_courses_dataset.csv")
        if _os.path.exists(courses_path):
            if courses is None:
                courses = _pd.read_csv(courses_path, encoding="utf-8-sig")
                log.info(f"Courses loaded from CSV: {len(courses)} courses")
        else:
            log.warning("Courses dataset not found")
    except Exception as e:
        log.warning(f"Could not load courses: {e}")

    # Normalize experience_required everywhere (fixes Excel-corrupted "5-Feb" → "2-5")
    from utils.data_loader import _fix_experience
    if "experience_required" in jobs.columns:
        jobs["experience_required"] = jobs["experience_required"].apply(_fix_experience)
    if engine.content_model.jobs_ref is not None and \
       "experience_required" in engine.content_model.jobs_ref.columns:
        engine.content_model.jobs_ref["experience_required"] = \
            engine.content_model.jobs_ref["experience_required"].apply(_fix_experience)

=======
    init_routes(engine, users, jobs, courses)
    log.info("JobNest API is ready!")

    yield

    log.info("Server shutting down...")


app = FastAPI(
    title       = "JobNest Recommendation API",
    description = "AI-powered job recommendation system using TF-IDF + ML hybrid engine",
    version     = "1.0.0",
    lifespan    = lifespan,
)

# Allow Flutter/React frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

app.include_router(router)


@app.get("/", tags=["General"])
def root():
    """Health check — visit /docs to test all endpoints."""
    return {
        "service" : "JobNest Recommendation API",
        "version" : "1.0.0",
        "status"  : "running",
        "docs"    : "http://127.0.0.1:8000/docs",
    }
