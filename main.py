from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional
import requests
import time
import os
from dotenv import load_dotenv
import urllib.parse

load_dotenv()
API_KEY = os.getenv("SERP_API_KEY")

app = FastAPI(title="Job Scraper API", version="1.0")

BASE_URL = "https://serpapi.com/search"

class Job(BaseModel):
    title: str
    company_name: str
    location: str
    via: Optional[str] = None
    description: Optional[str] = None
    job_id: Optional[str] = None
    link: str
    page: int
    extensions: Optional[dict] = {}

@app.get("/")
def read_root():
    return {"message": "Welcome to the Job Scraper API. Go to /docs to try it out."}

@app.get("/search-jobs", response_model=List[Job])
def search_jobs(query: str = Query(...),
                location: str = Query(...),
                pages: int = Query(1)):

    all_jobs = []
    page = 0
    next_page_token = None

    while page < pages:
        params = {
            "engine": "google_jobs",
            "q": f"{query} in {location}",
            "location": location,
            "google_domain": "google.com",
            "hl": "en",
            "api_key": API_KEY
        }

        if next_page_token:
            params["next_page_token"] = next_page_token

        try:
            response = requests.get(BASE_URL, params=params)
            data = response.json()

            if "error" in data:
                return [{
                    "title": f"Error: {data['error']}",
                    "company_name": "",
                    "location": "",
                    "link": "",
                    "page": page + 1
                }]

            if "jobs_results" not in data:
                break

            jobs = data["jobs_results"]
            for job in jobs:
                title = job.get("title", "")
                company = job.get("company_name", "")
                location_ = job.get("location", "")
                query_str = f"{title} at {company} in {location_}"
                search_link = f"https://www.google.com/search?q={urllib.parse.quote(query_str)}"

                job_data = {
                    "title": title,
                    "company_name": company,
                    "location": location_,
                    "via": job.get("via", ""),
                    "description": job.get("description", ""),
                    "job_id": job.get("job_id", ""),
                    "link": job.get("link", "") or search_link,
                    "page": page + 1,
                    "extensions": job.get("detected_extensions", {})
                }
                all_jobs.append(job_data)

            page += 1
            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break
            time.sleep(2)

        except Exception as e:
            return [{
                "title": f"Error: {str(e)}",
                "company_name": "",
                "location": "",
                "link": "",
                "page": page + 1
            }]
    
    return all_jobs
