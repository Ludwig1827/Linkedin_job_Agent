import json
import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urljoin
import os

def load_collected_jobs(filename="collected_jobs.json"):
    """Load the collected jobs from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {filename} not found. Please run get_jobs.py first.")
        return []

def fetch_job_description(job_url, session):
    """Fetch job description from LinkedIn job URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = session.get(job_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract job description - LinkedIn uses various selectors
        job_description = ""
        
        # Try different selectors for job description
        selectors = [
            '.description__text',
            '.show-more-less-html__markup',
            '.jobs-description-content__text',
            '.jobs-box__html-content',
            '[data-testid="job-details"]',
            '.jobs-description__container'
        ]
        
        for selector in selectors:
            desc_element = soup.select_one(selector)
            if desc_element:
                job_description = desc_element.get_text(strip=True)
                break
        
        # Extract additional job details
        job_details = {
            'title': None,
            'company': None,
            'location': None,
            'employment_type': None,
            'seniority_level': None,
            'description': job_description
        }
        
        # Extract title
        title_selectors = [
            '.top-card-layout__title',
            '.jobs-unified-top-card__job-title',
            'h1.t-24'
        ]
        
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                job_details['title'] = title_element.get_text(strip=True)
                break
        
        # Extract company
        company_selectors = [
            '.top-card-layout__card .top-card-layout__second-subline a',
            '.jobs-unified-top-card__company-name',
            '.top-card-layout__card .top-card-layout__second-subline'
        ]
        
        for selector in company_selectors:
            company_element = soup.select_one(selector)
            if company_element:
                job_details['company'] = company_element.get_text(strip=True)
                break
        
        # Extract location
        location_selectors = [
            '.top-card-layout__card .top-card-layout__third-subline',
            '.jobs-unified-top-card__bullet'
        ]
        
        for selector in location_selectors:
            location_element = soup.select_one(selector)
            if location_element:
                job_details['location'] = location_element.get_text(strip=True)
                break
        
        return job_details
        
    except requests.RequestException as e:
        print(f"Error fetching {job_url}: {e}")
        return None
    except Exception as e:
        print(f"Error parsing {job_url}: {e}")
        return None

def fetch_all_job_descriptions(jobs_data, output_file="jobs_with_descriptions.json"):
    """Fetch job descriptions for all jobs and save to file"""
    
    session = requests.Session()
    jobs_with_descriptions = []
    
    print(f"Fetching job descriptions for {len(jobs_data)} jobs...")
    
    for i, job in enumerate(jobs_data, 1):
        print(f"Processing job {i}/{len(jobs_data)}: {job['job_id']}")
        
        # Add delay to avoid rate limiting
        time.sleep(random.uniform(2, 5))
        
        job_details = fetch_job_description(job['url'], session)
        
        if job_details:
            # Merge original job data with fetched details
            updated_job = {
                **job,
                **job_details
            }
            jobs_with_descriptions.append(updated_job)
            print(f"✓ Successfully fetched: {job_details.get('title', 'Unknown Title')}")
        else:
            # Keep original job data even if fetch failed
            jobs_with_descriptions.append(job)
            print(f"✗ Failed to fetch job description for {job['job_id']}")
        
        # Save progress every 5 jobs
        if i % 5 == 0:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(jobs_with_descriptions, f, indent=2, ensure_ascii=False)
            print(f"Progress saved: {i}/{len(jobs_data)} jobs processed")
    
    # Save final results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(jobs_with_descriptions, f, indent=2, ensure_ascii=False)
    
    print(f"\nCompleted! Job descriptions saved to {output_file}")
    return jobs_with_descriptions

def main():
    # Load collected jobs
    jobs_data = load_collected_jobs()
    
    if not jobs_data:
        return
    
    print(f"Loaded {len(jobs_data)} jobs from collected_jobs.json")
    
    # Fetch job descriptions
    jobs_with_descriptions = fetch_all_job_descriptions(jobs_data)
    
    # Print summary
    successful_fetches = sum(1 for job in jobs_with_descriptions if job.get('description'))
    print(f"\nSummary:")
    print(f"Total jobs: {len(jobs_with_descriptions)}")
    print(f"Successfully fetched descriptions: {successful_fetches}")
    print(f"Failed fetches: {len(jobs_with_descriptions) - successful_fetches}")

if __name__ == "__main__":
    main()