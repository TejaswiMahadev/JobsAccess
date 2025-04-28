from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from typing import List, Optional, Dict, Any

app = FastAPI(
    title="Active Jobs Search API",
    description="An API for searching active job listings",
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
    company_name: Optional[str] = None
    job_link: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    date_posted: Optional[str] = None

class JobSearchResponse(BaseModel):
    total_results: int
    jobs: List[JobDetail]

@app.get("/api/jobs/search", response_model=JobSearchResponse, tags=["Jobs"])
async def search_jobs(
    job_title: Optional[str] = Query(None, description="Job title to search for"),
    location: Optional[str] = Query(None, description="Location to search for jobs"),
    keywords: Optional[str] = Query(None, description="Keywords to search in job description"),
    limit: int = Query(10, description="Number of results to return", ge=1, le=50)
):
    """
    Search for active job listings based on job title, location, and keywords.
    
    - **job_title**: Optional job title to search for (e.g., "Data Engineer")
    - **location**: Optional location to search for jobs (e.g., "United States")
    - **keywords**: Optional keywords to search in job descriptions
    - **limit**: Number of results to return (default: 10, max: 50)
    """
    try:
        url = "https://active-jobs-db.p.rapidapi.com/active-ats-6m"
        
        querystring = {
            "description_type": "text"
        }
        
        # Add optional query parameters if provided
        if job_title:
            querystring["title"] = job_title
        if location:
            querystring["location"] = location
        if keywords:
            querystring["keywords"] = keywords
        if limit:
            querystring["limit"] = str(limit)
        
        headers = {
            "x-rapidapi-key": "72b6266cf3msh141904a6b5b9345p195fabjsnc1247aee3b15",
            "x-rapidapi-host": "active-jobs-db.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        job_data = response.json()
        
        # Process the response data
        processed_jobs = process_job_data(job_data, limit)
        
        return {
            "total_results": len(processed_jobs),
            "jobs": processed_jobs
        }
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job data: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

def process_job_data(job_data: Dict[str, Any], limit: int) -> List[JobDetail]:
    """Process API response data to extract job details."""
    extracted_jobs = []
    
    # Check if we received job listings
    if not isinstance(job_data, dict):
        return []
    
    # Extract jobs array if it exists
    jobs_list = []
    if isinstance(job_data, list):
        jobs_list = job_data[:limit]
    elif isinstance(job_data, dict):
        if "jobs" in job_data and isinstance(job_data["jobs"], list):
            jobs_list = job_data["jobs"][:limit]
        else:
            # Some APIs might return the results directly in the root
            for key, value in job_data.items():
                if isinstance(value, list):
                    jobs_list = value[:limit]
                    break
    
    if not jobs_list:
        return []
    
    # Common field mappings for different API response structures
    title_keys = ['title', 'job_title', 'jobTitle', 'position', 'role']
    company_keys = ['company', 'company_name', 'companyName', 'employer', 'organization']
    link_keys = ['url', 'link', 'job_url', 'jobUrl', 'apply_link', 'application_link']
    location_keys = ['location', 'job_location', 'jobLocation', 'area', 'place']
    desc_keys = ['description', 'job_description', 'jobDescription', 'details', 'summary']
    date_keys = ['date', 'date_posted', 'datePosted', 'posted_date', 'postDate']
    
    for job in jobs_list:
        if not isinstance(job, dict):
            continue
            
        # Extract job details using the field mappings
        job_title = extract_value(job, title_keys) or "N/A"
        company_name = extract_value(job, company_keys)
        job_link = extract_value(job, link_keys)
        location = extract_value(job, location_keys)
        description = extract_value(job, desc_keys)
        date_posted = extract_value(job, date_keys)
        
        job_details = JobDetail(
            job_title=job_title,
            company_name=company_name,
            job_link=job_link,
            location=location,
            description=description,
            date_posted=date_posted
        )
        
        extracted_jobs.append(job_details)
    
    return extracted_jobs

def extract_value(job_dict: Dict[str, Any], possible_keys: List[str]) -> Optional[str]:
    """Extract a value from a dictionary using multiple possible keys."""
    for key in possible_keys:
        if key in job_dict and job_dict[key]:
            return str(job_dict[key])
    return None

@app.get("/api/jobs/raw", tags=["Jobs"])
async def get_raw_job_data(
    job_title: Optional[str] = Query(None, description="Job title to search for"),
    location: Optional[str] = Query(None, description="Location to search for jobs"),
    keywords: Optional[str] = Query(None, description="Keywords to search in job description")
):
    """
    Get raw job data from the active jobs API.
    This endpoint is useful for debugging or understanding the API response structure.
    """
    try:
        url = "https://active-jobs-db.p.rapidapi.com/active-ats-6m"
        
        querystring = {
            "description_type": "text"
        }
        
        # Add optional query parameters if provided
        if job_title:
            querystring["title"] = job_title
        if location:
            querystring["location"] = location
        if keywords:
            querystring["keywords"] = keywords
        
        headers = {
            "x-rapidapi-key": "72b6266cf3msh141904a6b5b9345p195fabjsnc1247aee3b15",
            "x-rapidapi-host": "active-jobs-db.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job data: {str(e)}")

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint that returns API information."""
    return {
        "message": "Welcome to the Active Jobs Search API",
        "documentation": "/docs",
        "endpoints": {
            "search_jobs": "/api/jobs/search",
            "raw_data": "/api/jobs/raw"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
