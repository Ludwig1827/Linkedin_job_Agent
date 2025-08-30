import json
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode, quote
import time
from dataclasses import dataclass
from openai import OpenAI
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re
import random
import urllib.parse
from typing import Optional, Dict, Any

load_dotenv(override=True)

# paramaters for Linkedin
distance =25
f_TPR = 'r86400'
geoId = 103644278
keywords = "AI%20Engineer"
location = "United%20States"
origin = "JOB_SEARCH_PAGE_JOB_FILTER"
sortBy = "R" # "DD" for date posted, "R" for relevance
f_E = 4 # 1 for internship, 2 for entry level, 3 for associate, 4 for mid-senior, 5 for director, 6 for executive
f_SB2 = 1 # 1 for 40k, 2 for 60k, 3 for 80k, 4 for 100k, 5 for 120k, 6 for 140k, 7 for 160k, 8 for 180k, 9 for 200k

def generate_linkedin_job_url(
    keywords: str = "AI Engineer",
    geoId: str = "103644278",
    location: str = "United States",
    distance: int = 25,
    f_TPR: str = "r86400",  # Time period filter
    sortBy: str = "R",      # Sort by (R=relevance, DD=date posted)
    f_E: int = 4,           # Experience level
    f_SB2: int = 1,         # Salary range
    origin: str = "JOB_SEARCH_PAGE_JOB_FILTER",
    refresh: bool = True,
    currentJobId: Optional[str] = None,
    **additional_params
) -> str:
    """
    Generate a LinkedIn job search URL with specified parameters.
    
    Args:
        keywords: Search keywords (e.g., "AI Engineer")
        geoId: Geographic location ID (103644278 = United States)
        location: Location name (e.g., "United States")
        distance: Search radius in miles (default: 25)
        f_TPR: Time period filter options:
            - "" = any time
            - "r86400" = past 24 hours
            - "r604800" = past week
            - "r2592000" = past month
        sortBy: Sort order:
            - "R" = relevance
            - "DD" = date posted
        f_E: Experience level:
            - 1 = internship
            - 2 = entry level
            - 3 = associate
            - 4 = mid-senior
            - 5 = director
            - 6 = executive
        f_SB2: Salary range:
            - 1 = $40k+
            - 2 = $60k+
            - 3 = $80k+
            - 4 = $100k+
            - 5 = $120k+
            - 6 = $140k+
            - 7 = $160k+
            - 8 = $180k+
            - 9 = $200k+
        origin: Source of the search
        refresh: Force refresh results
        currentJobId: Specific job ID to highlight
        **additional_params: Any additional URL parameters
    
    Returns:
        Complete LinkedIn job search URL
    """
    
    base_url = "https://www.linkedin.com/jobs/search/"
    
    # Build parameters dictionary
    params = {
        "keywords": keywords,
        "geoId": geoId,
        "location": location,
        "distance": distance,
        "sortBy": sortBy,
        "f_E": f_E,
        "f_SB2": f_SB2,
        "origin": origin,
        "refresh": "true" if refresh else "false"
    }
    
    # Add time period filter if specified
    if f_TPR:
        params["f_TPR"] = f_TPR
    
    # Add current job ID if specified
    if currentJobId:
        params["currentJobId"] = currentJobId
    
    # Add any additional parameters
    params.update(additional_params)
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    # URL encode the parameters
    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    
    return f"{base_url}?{query_string}"


if __name__ == "__main__":
    # Example 1: Basic usage with your original parameters
    print("=== Example 1: Your Original Parameters ===")
    url1 = generate_linkedin_job_url()
    print(f"URL: {url1}")