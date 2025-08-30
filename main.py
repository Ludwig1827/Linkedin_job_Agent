from resume_handling import extract_text_from_pdf, get_info_from_text
from generate_url import generate_linkedin_job_url
from get_jobs import LinkedInJobCollector, collect_linkedin_job_ids
from get_jd import load_collected_jobs, fetch_job_description, fetch_all_job_descriptions
from resume_job_matcher import ResumeJobMatcher
import json
from dotenv import load_dotenv

load_dotenv(override=True)

# Sample PDF resume path
pdf_path = "Yutong-GenAI Engineer.pdf"

resume_text = extract_text_from_pdf(pdf_path)
print("extracted resume text successfully")

resume_json= get_info_from_text(resume_text)
print("extracted resume information successfully")

# Generate LinkedIn job search URL
linkedin_url = generate_linkedin_job_url(
    keywords="AI Engineer",
    geoId="103644278",  # United States
    location="United States",
    distance=25,
    f_TPR="r86400",  # Past 24 hours
    sortBy="R",      # Relevance
    f_E=4,           # Mid-senior level
    f_SB2=1          # $40k+
)

print(f"Generated LinkedIn job search URL: {linkedin_url}")

# Collect job data from LinkedIn
job_collector = LinkedInJobCollector(linkedin_url)

print("The browser will open for you to login manually")
jobs = collect_linkedin_job_ids(linkedin_url, max_jobs=10, headless=False)

print(f"Collected {len(jobs)} job IDs from LinkedIn")

# make the collected_jobs.json file
if jobs:
    with open("collected_jobs.json", "w") as f:
        json.dump(jobs, f, indent=4)
    print("Saved collected job IDs to collected_jobs.json")

jobs_json = "collected_jobs.json"

# Fetch job descriptions for collected jobs
jobs_data = load_collected_jobs(jobs_json)
if not jobs_data:
    print("No jobs found in collected_jobs.json")
    exit(1)
jobs_with_descriptions = fetch_all_job_descriptions(jobs_data, output_file="jobs_with_descriptions.json")

print(f"Fetched job descriptions for {len(jobs_with_descriptions)} jobs")

jd_files = "jobs_with_descriptions.json"

# Initialize ResumeJobMatcher
matcher = ResumeJobMatcher()
print("Initialized ResumeJobMatcher")

# Run analysis
results = matcher.analyze_all_jobs(jd_files, resume_text)
print("Analyzed all jobs against the resume")

# Save results to JSON file
with open("analysis_results.json", "w") as f:
    json.dump(results, f, indent=4)
print("Saved analysis results to analysis_results.json")

# Create and display summary report
report = matcher.create_summary_report(results)
print("Created summary report:")

# Save report to file
with open("job_match_report.txt", "w", encoding='utf-8') as f:
    f.write(report)

# print the report to console
print(report)








