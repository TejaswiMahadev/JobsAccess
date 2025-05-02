from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import requests
import time
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="Job Scraper API",
    description="API for scraping job listings from Google Jobs via SerpAPI",
    version="1.0.0"
)

class JobScraper:
    def __init__(self, api_key):
        """
        Initialize the JobScraper with your SERP API key
        
        Args:
            api_key (str): Your SERP API key
        """
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"
    
    def search_jobs(self, query, location, pages=1):
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
                "api_key": self.api_key
            }

            if next_page_token:
                params["next_page_token"] = next_page_token

            try:
                response = requests.get(self.base_url, params=params)
                data = response.json()

                if "error" in data:
                    raise HTTPException(status_code=400, detail=f"API Error: {data['error']}")

                if "jobs_results" not in data:
                    break

                jobs = data["jobs_results"]
                for job in jobs:
                    job["page"] = page + 1
                    all_jobs.append(job)

                page += 1
                next_page_token = data.get("next_page_token")
                if not next_page_token:
                    break
                time.sleep(2)  # Reduced sleep time for API

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")

        return all_jobs

    def parse_jobs(self, jobs):
        """
        Parse raw job data into a structured format
        
        Args:
            jobs (list): Raw job data from SERP API
            
        Returns:
            list: List of structured job dictionaries
        """
        parsed_jobs = []
        
        for job in jobs:
            parsed_job = {
                "title": job.get("title", ""),
                "company_name": job.get("company_name", ""),
                "location": job.get("location", ""),
                "via": job.get("via", ""),
                "description": job.get("description", ""),
                "job_id": job.get("job_id", ""),
                "detected_extensions": {},
                "link": job.get("link", "") or f"https://www.google.com/search?q={job.get('title', '')} at {job.get('company_name', '')} in {job.get('location', '')}",
                "page": job.get("page", 0)
            }
            if "detected_extensions" in job:
                extensions = job["detected_extensions"]
                for key, value in extensions.items():
                    parsed_job["detected_extensions"][key] = value
            
            parsed_jobs.append(parsed_job)
            
        return parsed_jobs

# Pydantic models for request and response
class JobSearchRequest(BaseModel):
    query: str = Field(..., description="Job title or keywords")
    location: str = Field(..., description="Location for job search")
    pages: int = Field(1, description="Number of pages to scrape", ge=1, le=5)

class JobResult(BaseModel):
    title: str
    company_name: str
    location: str
    via: str = ""
    description: str
    job_id: str = ""
    link: str
    page: int
    detected_extensions: Dict[str, Any] = {}

class JobSearchResponse(BaseModel):
    total_jobs: int
    jobs: List[JobResult]

# Get API key from environment variable
def get_api_key():
    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="SERP_API_KEY environment variable is not set. Please set it in your .env file or environment variables."
        )
    return api_key

@app.get("/")
def read_root():
    return {"message": "Welcome to Job Scraper API. Visit /docs for API documentation."}

@app.post("/search/", response_model=JobSearchResponse)
def search_jobs(request: JobSearchRequest, api_key: str = Depends(get_api_key)):
    scraper = JobScraper(api_key)
    raw_jobs = scraper.search_jobs(
        query=request.query,
        location=request.location,
        pages=request.pages
    )
    parsed_jobs = scraper.parse_jobs(raw_jobs)
    
    return {
        "total_jobs": len(parsed_jobs),
        "jobs": parsed_jobs
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
