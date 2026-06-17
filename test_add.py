import warnings
warnings.filterwarnings("ignore")

from fastapi.testclient import TestClient
from app import app
import json

new_job = {
    "company_name": "Google DeepMind",
    "title": "Senior AI Agent Engineer",
    "job_required_skills": "Python|FastAPI|LLMs|Agents",
    "job_location": "Remote",
    "industry": "Artificial Intelligence",
    "job_type": "Full Time",
    "salary_range_egp": "50000-100000",
    "experience_required": "5",
    "description": "Building the next generation of autonomous coding agents."
}

print("Starting TestClient (this will trigger app lifespan to load models)...")
with TestClient(app) as client:
    print("\n1. Sending POST /api/jobs/new...")
    response = client.post("/api/jobs/new", json=new_job)
    print("POST Response Status:", response.status_code)
    print("POST Response Body:", json.dumps(response.json(), indent=2, ensure_ascii=False))

    job_id = response.json().get("job_id")
    if job_id:
        print(f"\n2. Verifying job {job_id} in TF-IDF matrix via GET /api/jobs/{job_id}/score...")
        res_verify = client.get(f"/api/jobs/{job_id}/score")
        print("GET Response Status:", res_verify.status_code)
        print("GET Response Body:", json.dumps(res_verify.json(), indent=2, ensure_ascii=False))
