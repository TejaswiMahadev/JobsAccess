from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from typing import List, Optional

app = FastAPI(
    title="LinkedIn Job Search API",
    description="An API for searching LinkedIn job listings",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define response models
class JobDetail(BaseModel):
    job_title: str
    company_name: str
    job_link: str
    location: Optional[str] = None
    date_posted: Optional[str] = None

class JobSearchResponse(BaseModel):
    total_results: int
    jobs: List[JobDetail]

@app.get("/api/jobs/search", response_model=JobSearchResponse, tags=["Jobs"])
async def search_jobs(
    job_title: str = Query(..., description="Job title to search for"),
    location: str = Query(..., description="Location to search for jobs"),
    limit: int = Query(10, description="Number of results to return", ge=1, le=50)
):
    """
    Search for LinkedIn job listings based on job title and location.
    
    - **job_title**: Job title to search for (e.g., "Data Engineer", "Software Developer")
    - **location**: Location to search for jobs (e.g., "United States", "Remote", "London")
    - **limit**: Number of results to return (default: 10, max: 50)
    """
    try:
        url = "https://linkedin-job-search-api.p.rapidapi.com/active-jb-7d"
        
        formatted_title = f'"{job_title}"'
        formatted_location = f'"{location}"'
        
        querystring = {
            "limit": str(limit),
            "offset": "0",
            "title_filter": formatted_title,
            "location_filter": formatted_location
        }
        
        headers = {
            "x-rapidapi-key": "RAPID_API_KEY",
            "x-rapidapi-host": "linkedin-job-search-api.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        linkedin_data = response.json()
        
        # Process the response data
        processed_jobs = process_job_data(linkedin_data)
        
        return {
            "total_results": len(processed_jobs),
            "jobs": processed_jobs
        }
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job data: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

def process_job_data(linkedin_data):
    """Process LinkedIn API response data to extract job details."""
    extracted_jobs = []
    
    if isinstance(linkedin_data, list):
        jobs_list = linkedin_data
    elif isinstance(linkedin_data, dict) and 'jobs' in linkedin_data:
        jobs_list = linkedin_data['jobs']
    else:
        return []
    
    company_keys = ['company_name', 'company', 'companyName', 'employer', 'organization', 'firm']
    link_keys = ['url', 'link', 'job_url', 'jobUrl', 'application_url', 'listing_url']
    location_keys = ['location', 'job_location', 'jobLocation', 'area']
    date_keys = ['date_posted', 'datePosted', 'posted_date', 'post_date', 'listed_date']
    
    for job in jobs_list:
        company_name = extract_value(job, company_keys)
        job_link = extract_value(job, link_keys)
        location = extract_value(job, location_keys)
        date_posted = extract_value(job, date_keys)
        
        job_details = JobDetail(
            job_title=job.get('title', 'N/A'),
            company_name=company_name,
            job_link=job_link,
            location=location,
            date_posted=date_posted
        )
        
        extracted_jobs.append(job_details)
    
    return extracted_jobs

def extract_value(job_dict, possible_keys):
    """Extract a value from a dictionary using multiple possible keys."""
    for key in possible_keys:
        if key in job_dict and job_dict[key]:
            return job_dict[key]
    return None

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint that returns API information."""
    return {
        "message": "Welcome to the LinkedIn Job Search API",
        "documentation": "/docs",
        "endpoints": {
            "search_jobs": "/api/jobs/search?job_title={job_title}&location={location}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
