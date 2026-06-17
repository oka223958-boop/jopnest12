# JobNest — AI Job Recommendation API

JobNest is an AI-powered job recommendation system that combines:

- Content-based matching using TF‑IDF + cosine similarity (fast filtering)
- A machine-learning classifier (Random Forest + Gradient Boosting) to estimate job fit
- A hybrid scoring strategy to rank results

In addition to recommendations, JobNest supports **dynamic ingestion** of new jobs, users, and courses via API endpoints, and **persists** them to disk (pickle caches) so they survive server restarts.

---

## What does it do?

- Recommend jobs for an existing user (`/api/recommend`)
- Recommend jobs for an anonymous user profile (`/api/recommend/realtime`)
- List/search users and jobs
- Recommend courses based on user skills (`/api/courses/recommend`)
- Ingest new records live (no restart needed):
  - Add job: `POST /api/jobs/new` (updates TF‑IDF matrix incrementally)
  - Add user: `POST /api/users/new`
  - Add course: `POST /api/courses/new`
- Persist dynamic changes to disk:
  - `data/jobs_cache.pkl`, `data/users_cache.pkl`, `data/courses_cache.pkl`

---

## Project structure (high level)

```
.
├── api/
│   └── routes.py                 # FastAPI endpoints
├── chatbot/
│   └── engine.py                 # Keyword-based chatbot + personalization
├── config/
│   └── settings.py               # Paths + constants
├── data/
│   ├── jobnest_enhanced_dataset.csv
│   └── jobnest_courses_dataset.csv
├── models/
│   ├── content_model.py          # TF-IDF model (incremental updates supported)
│   ├── ml_model.py               # ML classifier
│   ├── hybrid_engine.py          # Hybrid recommender
│   └── saved/                    # Saved models + TF-IDF artifacts
├── utils/
│   ├── data_loader.py            # Load/build base tables from CSV + caches
│   ├── feature_engineering.py    # ML features
│   ├── persistence.py            # Save/load dynamic caches (.pkl)
│   └── logger.py                 # Logging
├── app.py                        # FastAPI app entrypoint
├── train.py                      # Train models + save to disk
└── requirements.txt
```

---

## Setup (Windows)

### Prerequisites

- Python installed (this project has been used with Python 3.14 on Windows)

### Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Put datasets in `data/`

- `data/jobnest_enhanced_dataset.csv`
- `data/jobnest_courses_dataset.csv`

### Train models (first time)

```bash
python train.py
```

### Run the API

Recommended (works even if `uvicorn` is not on PATH):

```bash
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI:

- `http://127.0.0.1:8000/docs`

---

## Main API endpoints (quick reference)

### Health

- `GET /api/health`

### Recommendations

- `POST /api/recommend`
- `POST /api/recommend/realtime`

### Jobs

- `GET /api/jobs`
- `POST /api/jobs/new`
- `GET /api/jobs/{job_id}/score` (verifies TF‑IDF indexing)

### Users

- `GET /api/user/{user_id}`
- `GET /api/user/search`
- `POST /api/users/new`

### Courses

- `GET /api/courses`
- `POST /api/courses/recommend`
- `POST /api/courses/new`

---

## Example: add a new course

```json
{
  "title": "FastAPI from Scratch",
  "specialty": "Backend Development",
  "platform": "YouTube",
  "level": "Beginner",
  "language": "English",
  "price": "Free",
  "rating": 4.8,
  "skills": "Python|FastAPI|REST",
  "instructor": "JobNest",
  "duration": "6 hours",
  "certificate": "No",
  "url": "https://example.com/course"
}
```