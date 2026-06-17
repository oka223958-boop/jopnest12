"""
==============================================================
  api/routes.py  —  FastAPI Route Definitions
  Chatbot: keyword-based engine (no API key needed)
==============================================================
"""

import os
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from utils.logger import get_logger
from utils.persistence import save_all, save_users, save_courses
from chatbot.engine import ChatbotEngine

log    = get_logger(__name__)
router = APIRouter()

_engine  = None
_users   = None
_jobs    = None
_courses = None
_chatbot = None


def init_routes(engine, users, jobs, courses=None):
    global _engine, _users, _jobs, _courses, _chatbot
    _engine  = engine
    _users   = users
    _jobs    = jobs
    _courses = courses if courses is not None else pd.DataFrame()
    _chatbot = ChatbotEngine(_jobs, _users, _courses, _engine)
    log.info("Routes initialized")


class RecommendRequest(BaseModel):
    user_id  : Optional[int] = Field(None, example=1307)
    user_name: Optional[str] = Field(None, example="Magdy Mansour")
    top_n    : int           = Field(default=10, ge=1, le=50)

class RealtimeRequest(BaseModel):
    user_skills        : str = Field(..., example="Python|Django|SQL")
    cv_summary         : str = Field("", example="Backend developer")
    user_location      : str = Field("Unknown", example="Cairo")
    experience_years   : int = Field(0, ge=0, example=3)
    preferred_job_type : str = Field("", example="Remote|Full Time")
    expected_salary_egp: str = Field("0-0", example="10000-20000")
    top_n              : int = Field(default=10, ge=1, le=50)

class ChatRequest(BaseModel):
    message : str           = Field(..., example="عايز وظيفة flutter remote")
    user_id : Optional[int] = Field(None, example=1307)
    top_n   : int           = Field(default=5, ge=1, le=20)
    context : Optional[list]= Field(None)


class NewJobRequest(BaseModel):
    """Schema for adding a new job/company to the live jobs pool."""
    company_name       : str            = Field(...,  example="Acme Corp")
    title              : str            = Field(...,  example="Software Engineer")
    job_required_skills: str            = Field(...,  example="Python|FastAPI|SQL")
    job_location       : str            = Field("Remote", example="Cairo")
    industry           : str            = Field("Technology", example="FinTech")
    job_type           : str            = Field("Full Time", example="Remote")
    salary_range_egp   : str            = Field("0-0",  example="15000-25000")
    experience_required: str            = Field("0",   example="2")
    description        : Optional[str]  = Field("",    example="We are looking for...")


class NewUserRequest(BaseModel):
    """Schema for adding a new user to the live users pool."""
    user_name          : str = Field(..., example="Magdy Mansour")
    user_skills        : str = Field(..., example="Python|Django|SQL")
    role               : str = Field(..., example="Backend Developer")
    user_location      : str = Field("Unknown", example="Cairo")
    experience_years   : int = Field(0, ge=0, example=3)
    preferred_job_type : str = Field("", example="Remote|Full Time")
    expected_salary_egp: str = Field("0-0", example="10000-20000")


class NewCourseRequest(BaseModel):
    """Schema for adding a new course to the live courses pool."""
    title     : str           = Field(..., example="Python for Everybody")
    specialty : str           = Field(..., example="Data Science")
    platform  : str           = Field("Unknown", example="Coursera")
    level     : str           = Field("Beginner", example="Beginner")
    language  : str           = Field("English", example="Arabic")
    price     : str           = Field("Free", example="Free")
    rating    : float         = Field(0.0, ge=0.0, le=5.0, example=4.7)
    skills    : str           = Field("", example="Python|Pandas|NumPy")
    instructor: Optional[str] = Field("", example="Andrew Ng")
    duration  : Optional[str] = Field("", example="20 hours")
    certificate: Optional[str] = Field("", example="Yes")
    url       : Optional[str] = Field("", example="https://example.com/course")


@router.get("/api/health", tags=["General"])
def health():
    return {"status": "ok", "models_loaded": _engine is not None,
            "total_jobs": len(_jobs) if _jobs is not None else 0,
            "total_users": len(_users) if _users is not None else 0,
            "total_courses": len(_courses) if _courses is not None else 0}


@router.post("/api/recommend", tags=["Recommendations"])
def recommend(body: RecommendRequest):
    if body.user_id is None and body.user_name is None:
        raise HTTPException(status_code=400, detail="Provide either user_id or user_name")
    if body.user_id is not None:
        user_row = _users[_users["user_id"] == body.user_id]
        not_found_msg = f"User {body.user_id} not found"
    else:
        user_row = _users[_users["user_name"].str.contains(body.user_name, case=False, na=False)]
        not_found_msg = f"No user: '{body.user_name}'"
    if user_row.empty:
        raise HTTPException(status_code=404, detail=not_found_msg)
    if len(user_row) > 1:
        return {"message": "Multiple users — pick a user_id", "total_found": len(user_row),
                "users": user_row[["user_id","user_name","role","user_location","user_skills"]].to_dict(orient="records")}
    user = user_row.iloc[0]
    try:
        recs = _engine.recommend(user, _jobs, top_n=body.top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Recommendation engine error")
    return {"user_id": int(user["user_id"]), "user_name": user["user_name"],
            "total_results": len(recs), "recommendations": _format_jobs(recs)}


@router.post("/api/recommend/realtime", tags=["Recommendations"])
def recommend_realtime(body: RealtimeRequest):
    user = pd.Series({"user_id": 0, "user_name": "Anonymous",
                       "user_skills": body.user_skills, "cv_summary": body.cv_summary,
                       "user_location": body.user_location, "experience_years": body.experience_years,
                       "preferred_job_type": body.preferred_job_type,
                       "expected_salary_egp": body.expected_salary_egp})
    try:
        recs = _engine.recommend(user, _jobs, top_n=body.top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Recommendation engine error")
    return {"user_id": 0, "user_name": "Anonymous",
            "total_results": len(recs), "recommendations": _format_jobs(recs)}


@router.get("/api/user/search", tags=["Users"])
def search_users(name: str = Query(..., example="Magdy"), limit: int = Query(10, ge=1, le=50)):
    mask = _users["user_name"].str.contains(name, case=False, na=False)
    results = _users[mask][["user_id","user_name","role","user_location","user_skills"]]
    if results.empty:
        raise HTTPException(status_code=404, detail=f"No users: '{name}'")
    return {"query": name, "total_found": len(results), "users": results.head(limit).to_dict(orient="records")}


@router.get("/api/user/{user_id}", tags=["Users"])
def get_user(user_id: int):
    row = _users[_users["user_id"] == user_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return row.iloc[0].to_dict()


@router.post("/api/users/new", tags=["Users"], status_code=201)
def add_new_user(body: NewUserRequest):
    """
    Add a new user to the live users pool.

    The user is appended immediately to the in-memory DataFrame.
    A unique user_id is auto-assigned (max existing id + 1).
    The updated users table is persisted to disk so it survives restarts.
    """
    global _users, _chatbot

    if _users is None:
        raise HTTPException(status_code=503, detail="Users data not loaded yet")

    # ── Auto-assign a unique user_id ─────────────────────────
    new_id = int(_users["user_id"].max()) + 1 if "user_id" in _users.columns else 1

    # ── Build the new row matching the existing schema ───────
    new_row = {
        "user_id"           : new_id,
        "user_name"         : body.user_name,
        "user_skills"       : body.user_skills,
        "role"              : body.role,
        "user_location"     : body.user_location,
        "experience_years"  : body.experience_years,
        "preferred_job_type": body.preferred_job_type,
        "expected_salary_egp": body.expected_salary_egp,
    }

    # ── Fill any extra columns that exist in _users with defaults
    for col in _users.columns:
        if col not in new_row:
            new_row[col] = ""

    # ── Append to the live DataFrame ─────────────────────────
    new_df = pd.DataFrame([new_row])
    _users = pd.concat([_users, new_df], ignore_index=True)

    # Keep chatbot in sync with the updated users DataFrame
    if _chatbot is not None:
        _chatbot.users = _users

    # ── Persist to disk so new user survives a restart ───────
    try:
        save_users(_users)
    except Exception as e:
        log.warning(f"User persistence skipped: {e}")

    log.info(f"New user added: user_id={new_id} | '{body.user_name}'")

    return {
        "status": "created",
        "user_id": new_id,
        "message": f"User '{body.user_name}' added successfully.",
    }


@router.get("/api/jobs", tags=["Jobs"])
def list_jobs(industry: Optional[str]=Query(None), type: Optional[str]=Query(None),
              title: Optional[str]=Query(None), limit: int=Query(20, ge=1, le=100)):
    filtered = _jobs.copy()
    if industry: filtered = filtered[filtered["industry"].str.lower() == industry.lower()]
    if type    : filtered = filtered[filtered["job_type"].str.lower() == type.lower()]
    if title   : filtered = filtered[filtered["title"].str.contains(title, case=False, na=False)]
    return {"total": len(filtered), "showing": min(limit, len(filtered)),
            "jobs": filtered.head(limit).to_dict(orient="records")}


@router.post("/api/jobs/new", tags=["Jobs"], status_code=202)
def add_new_job(body: NewJobRequest, background_tasks: BackgroundTasks):
    """
    Add a new company/job to the live jobs pool.

    The job is appended immediately to the in-memory DataFrame so
    it becomes eligible for recommendations on the next request.
    A unique job_id is auto-assigned (max existing id + 1).

    Returns 202 Accepted with the assigned job_id.
    """
    global _jobs

    if _jobs is None:
        raise HTTPException(status_code=503, detail="Jobs data not loaded yet")

    # ── Auto-assign a unique job_id ──────────────────────────
    new_id = int(_jobs["job_id"].max()) + 1 if "job_id" in _jobs.columns else 1

    # ── Build the new row matching the existing schema ───────
    new_row = {
        "job_id"             : new_id,
        "company_name"       : body.company_name,
        "title"              : body.title,
        "job_required_skills": body.job_required_skills,
        "job_location"       : body.job_location,
        "industry"           : body.industry,
        "job_type"           : body.job_type,
        "salary_range_egp"   : body.salary_range_egp,
        "experience_required": body.experience_required,
        "description"        : body.description or "",
    }

    # ── Fill any extra columns that exist in _jobs with defaults
    for col in _jobs.columns:
        if col not in new_row:
            new_row[col] = ""

    # ── Append to the live DataFrame ─────────────────────────
    new_df = pd.DataFrame([new_row])
    _jobs  = pd.concat([_jobs, new_df], ignore_index=True)
    if _chatbot is not None:
        _chatbot.jobs = _jobs

    # ── Update TF-IDF matrix so the new job is rankable NOW ──
    # add_job() uses the frozen vectorizer → no retraining needed.
    if _engine is not None and _engine.content_model.job_matrix is not None:
        try:
            _engine.content_model.add_job(pd.Series(new_row))
            log.info(f"TF-IDF matrix updated with job_id={new_id}")
        except Exception as e:
            log.warning(f"TF-IDF update skipped: {e}")

    # ── Persist to disk so new job survives a restart ─────────
    try:
        save_all(_jobs, _engine.content_model)
    except Exception as e:
        log.warning(f"Persistence skipped: {e}")

    log.info(f"New job added: job_id={new_id} | '{body.title}' @ {body.company_name}")

    # ── Background Task: Calculate ML scores for all users ───
    # We do not block the API response for this.
    background_tasks.add_task(_rank_new_job_background, new_id, new_row)

    return {
        "status" : "accepted",
        "job_id" : new_id,
        "message": f"Job '{body.title}' at '{body.company_name}' added successfully. "
                   f"It is now included in the recommendation pool.",
    }


def _rank_new_job_background(job_id: int, new_row: dict):
    """
    Background task to calculate ML scores for the newly added job against ALL users.
    (This is an example logic - for a real system, you might only rank on-demand
    or rank against a sample of users to avoid heavy computation).
    """
    if _engine is None or _engine.ml_model is None or _users is None:
        return

    log.info(f"Background ML scoring started for job_id={job_id}...")
    try:
        # 1. Convert to DataFrame (engine expects df)
        job_df = pd.DataFrame([new_row])

        # 2. In a real scenario, you'd calculate this for all users.
        #    For demonstration, we just log that we would do it, or we could
        #    pre-compute it for active users. Since the recommend() endpoint
        #    computes ML score *on the fly* for the top-50 content candidates,
        #    we actually don't NEED to pre-compute it here!
        #
        #    The endpoint flow is:
        #      1. Content model gets top-50 (this works because we updated the TF-IDF matrix)
        #      2. ML model scores those 50 ON THE FLY in _score_with_ml()
        #
        #    So, there's no strict requirement to pre-compute ML scores here,
        #    as long as the job is in the content matrix.
        #
        #    However, if we had a caching layer or pre-computed user recommendations,
        #    we would update it here.
        log.info(f"Background ML scoring completed for job_id={job_id}. "
                 f"(No pre-computation needed as recommend() scores on-the-fly).")

    except Exception as e:
        log.error(f"Error in background ML scoring for job_id={job_id}: {e}")


@router.get("/api/jobs/{job_id}/score", tags=["Jobs"])
def verify_job_indexing(job_id: int):
    """
    Verification endpoint to check if a specific job is present in the 
    live `_jobs` DataFrame and if it has been indexed in the TF-IDF matrix.
    """
    if _jobs is None or _engine is None or _engine.content_model is None:
        raise HTTPException(status_code=503, detail="System not fully initialized")

    # 1. Check if job exists in _jobs DataFrame
    job_rows = _jobs[_jobs["job_id"] == job_id]
    if job_rows.empty:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found in live data")
    
    job_data = job_rows.iloc[0]

    # 2. Check if job is in the TF-IDF jobs_ref
    in_tfidf = False
    matrix_size = 0
    if _engine.content_model.jobs_ref is not None:
        ref_rows = _engine.content_model.jobs_ref[_engine.content_model.jobs_ref["job_id"] == job_id]
        in_tfidf = not ref_rows.empty
    
    if _engine.content_model.job_matrix is not None:
        matrix_size = _engine.content_model.job_matrix.shape[0]

    return {
        "job_id": int(job_id),
        "title": job_data.get("title", ""),
        "company_name": job_data.get("company_name", ""),
        "in_live_dataframe": True,
        "in_tfidf_matrix": in_tfidf,
        "matrix_size": matrix_size
    }

@router.post("/api/chat", tags=["Chatbot"])
def chat(body: ChatRequest):
    """
    AI Chatbot — Arabic & English. No API key needed.
    Examples:
    - { "message": "عايز وظيفة flutter remote" }
    - { "message": "Recommend beginner Python courses" }
    - { "message": "What is machine learning?" }
    - { "message": "I want a flutter track" }
    - { "message": "CV tips" }
    """
    if _chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    return _chatbot.chat(message=body.message, user_id=body.user_id,
                         top_n=body.top_n, context=body.context or [])


@router.get("/api/courses", tags=["Courses"])
def list_courses(specialty: Optional[str]=Query(None), platform: Optional[str]=Query(None),
                 level: Optional[str]=Query(None), language: Optional[str]=Query(None),
                 free: Optional[bool]=Query(None), limit: int=Query(20, ge=1, le=100)):
    if _courses is None or _courses.empty:
        raise HTTPException(status_code=503, detail="Courses not loaded")
    filtered = _courses.copy()
    if specialty: filtered = filtered[filtered["specialty"].str.lower() == specialty.lower()]
    if platform : filtered = filtered[filtered["platform"].str.lower()  == platform.lower()]
    if level    : filtered = filtered[filtered["level"].str.lower()     == level.lower()]
    if language : filtered = filtered[filtered["language"].str.lower()  == language.lower()]
    if free     : filtered = filtered[filtered["price"].str.lower().isin(["free","مجاني"])]
    filtered = filtered.sort_values("rating", ascending=False)
    return {"total": len(filtered), "showing": min(limit, len(filtered)),
            "courses": filtered.head(limit).to_dict(orient="records")}


@router.post("/api/courses/recommend", tags=["Courses"])
def recommend_courses(body: RecommendRequest):
    if _courses is None or _courses.empty:
        raise HTTPException(status_code=503, detail="Courses not loaded")
    if body.user_id is None and body.user_name is None:
        raise HTTPException(status_code=400, detail="Provide user_id or user_name")
    if body.user_id is not None:
        user_row = _users[_users["user_id"] == body.user_id]
    else:
        user_row = _users[_users["user_name"].str.contains(body.user_name, case=False, na=False)]
    if user_row.empty:
        raise HTTPException(status_code=404, detail="User not found")
    if len(user_row) > 1:
        return {"message": "Multiple users — pick a user_id",
                "users": user_row[["user_id","user_name","role"]].to_dict(orient="records")}
    user   = user_row.iloc[0]
    skills = str(user.get("user_skills","")).lower().split("|")
    def skill_match(cs):
        return any(sk.strip() in str(cs).lower() for sk in skills if sk.strip())
    filtered = _courses[_courses["skills"].apply(skill_match)]
    if filtered.empty: filtered = _courses.copy()
    filtered = filtered.sort_values("rating", ascending=False).head(body.top_n)
    return {"user_id": int(user["user_id"]), "user_name": user["user_name"],
            "user_skills": user.get("user_skills",""),
            "total_results": len(filtered), "recommendations": filtered.to_dict(orient="records")}


@router.post("/api/courses/new", tags=["Courses"], status_code=201)
def add_new_course(body: NewCourseRequest):
    """
    Add a new course to the live courses pool.

    The course is appended immediately to the in-memory DataFrame.
    A unique course_id is auto-assigned (max existing id + 1).
    The updated courses table is persisted to disk so it survives restarts.
    """
    global _courses, _chatbot

    if _courses is None or _courses.empty:
        raise HTTPException(status_code=503, detail="Courses not loaded")

    new_id = int(_courses["course_id"].max()) + 1 if "course_id" in _courses.columns else 1

    new_row = {
        "course_id"  : new_id,
        "title"      : body.title,
        "platform"   : body.platform,
        "instructor" : body.instructor or "",
        "specialty"  : body.specialty,
        "skills"     : body.skills or "",
        "level"      : body.level,
        "duration"   : body.duration or "",
        "price"      : body.price,
        "rating"     : body.rating,
        "language"   : body.language,
        "certificate": body.certificate or "",
        "url"        : body.url or "",
    }

    for col in _courses.columns:
        if col not in new_row:
            new_row[col] = ""

    new_df = pd.DataFrame([new_row])
    _courses = pd.concat([_courses, new_df], ignore_index=True)

    if _chatbot is not None:
        _chatbot.courses = _courses

    try:
        save_courses(_courses)
    except Exception as e:
        log.warning(f"Course persistence skipped: {e}")

    log.info(f"New course added: course_id={new_id} | '{body.title}'")
    return {
        "status": "created",
        "course_id": new_id,
        "message": f"Course '{body.title}' added successfully.",
    }


def _format_jobs(df):
    records = df[["job_id","title","company_name","industry","job_type","job_location",
                  "salary_range_egp","experience_required","job_required_skills",
                  "content_score","ml_score","final_score"]].to_dict(orient="records")
    return [{k: (float(v) if hasattr(v,"item") else v) for k,v in r.items()} for r in records]
