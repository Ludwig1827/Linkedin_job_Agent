import json
import openai
import os
from typing import List, Dict, Tuple
import re
from datetime import datetime
import pandas as pd
from resume_handling import extract_text_from_pdf, get_info_from_text
from dotenv import load_dotenv
load_dotenv(override=True)

class ResumeJobMatcher:
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        """
        Initialize the resume-job matcher with OpenAI API.
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY environment variable)
            model: OpenAI model to use for analysis
        """
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
        self.model = model
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for better analysis."""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove "Show more/Show less" artifacts
        text = re.sub(r'Show more.*?Show less', '', text, flags=re.IGNORECASE)
        
        return text
    
    def extract_key_info(self, job_description: str) -> Dict:
        """Extract key information from job description using AI."""
        
        prompt = f"""
        Analyze this job description and extract key information in JSON format:
        
        Job Description:
        {job_description}
        
        Extract:
        1. Required technical skills (programming languages, frameworks, tools)
        2. Required experience level (years)
        3. Key responsibilities
        4. Preferred qualifications
        5. Company type/industry
        6. Salary range (if mentioned)
        
        Return as JSON with keys: technical_skills, experience_years, responsibilities, preferred_qualifications, industry, salary_range
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert HR analyst. Extract job requirements accurately and return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
                
        except Exception as e:
            print(f"Error extracting job info: {e}")
            return {}
    
    def calculate_match_score(self, resume_text: str, job_description: str, job_title: str = "", company: str = "") -> Dict:
        """
        Calculate comprehensive match score between resume and job description.
        
        Args:
            resume_text: Your resume content
            job_description: Job description text
            job_title: Job title for context
            company: Company name for context
            
        Returns:
            Dictionary with match score and detailed analysis
        """
        
        prompt = f"""
        As an expert technical recruiter, analyze how well this resume matches the job requirements.
        
        RESUME:
        {resume_text}
        
        JOB DESCRIPTION:
        {job_description}
        
        JOB TITLE: {job_title}
        COMPANY: {company}
        
        Provide a comprehensive analysis with:
        
        1. OVERALL MATCH SCORE (0-100): Based on skills, experience, and requirements alignment
        
        2. DETAILED BREAKDOWN:
        - Technical Skills Match (0-100): How well technical skills align
        - Experience Level Match (0-100): Experience years and seniority fit
        - Domain Experience Match (0-100): Relevant industry/domain experience
        - Responsibilities Match (0-100): How past roles align with job duties
        
        3. STRENGTHS: Top 3-5 strongest matching points
        
        4. GAPS: Top 3-5 areas where resume doesn't match requirements
        
        5. KEYWORDS MISSING: Important keywords from job description not in resume
        
        6. RECOMMENDATIONS: Specific advice to improve match score
        
        7. APPLICATION PRIORITY: HIGH/MEDIUM/LOW based on match quality
        
        Format as JSON with keys: overall_score, technical_skills_score, experience_score, domain_score, responsibilities_score, strengths, gaps, missing_keywords, recommendations, priority
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert technical recruiter with 15+ years experience. Provide accurate, actionable analysis. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                
                # Add metadata
                analysis['job_title'] = job_title
                analysis['company'] = company
                analysis['analysis_timestamp'] = datetime.now().isoformat()
                
                return analysis
            else:
                return self._create_fallback_analysis(job_title, company)
                
        except Exception as e:
            print(f"Error calculating match score: {e}")
            return self._create_fallback_analysis(job_title, company)
    
    def _create_fallback_analysis(self, job_title: str, company: str) -> Dict:
        """Create fallback analysis if AI analysis fails."""
        return {
            "overall_score": 0,
            "technical_skills_score": 0,
            "experience_score": 0,
            "domain_score": 0,
            "responsibilities_score": 0,
            "strengths": ["Analysis failed - manual review needed"],
            "gaps": ["Could not analyze - check API connection"],
            "missing_keywords": [],
            "recommendations": ["Retry analysis or review manually"],
            "priority": "UNKNOWN",
            "job_title": job_title,
            "company": company,
            "analysis_timestamp": datetime.now().isoformat(),
            "error": "AI analysis failed"
        }
    
    def analyze_all_jobs(self, jobs_file: str, resume_text: str) -> List[Dict]:
        """
        Analyze all jobs from collected_jobs.json against resume.
        
        Args:
            jobs_file: Path to collected_jobs.json
            resume_text: Your resume content
            
        Returns:
            List of analysis results sorted by match score
        """
        
        # Load jobs data
        with open(jobs_file, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        
        print(f"🔍 Analyzing {len(jobs)} jobs against your resume...")
        
        results = []
        
        for i, job in enumerate(jobs, 1):
            job_id = job.get('job_id', 'unknown')
            job_title = job.get('title', 'No title')
            company = job.get('company', 'No company')
            description = self.clean_text(job.get('description', ''))
            
            print(f"📊 Analyzing {i}/{len(jobs)}: {job_title} at {company}")
            
            if not description:
                print(f"⚠️  No description found for job {job_id}")
                continue
            
            # Calculate match score
            analysis = self.calculate_match_score(
                resume_text=resume_text,
                job_description=description,
                job_title=job_title,
                company=company
            )
            
            # Add job metadata
            analysis['job_id'] = job_id
            analysis['job_url'] = job.get('url', '')
            
            results.append(analysis)
            
            print(f"   ✅ Match Score: {analysis.get('overall_score', 0)}/100 - Priority: {analysis.get('priority', 'UNKNOWN')}")
        
        # Sort by overall score (highest first)
        results.sort(key=lambda x: x.get('overall_score', 0), reverse=True)
        
        return results
    
    def save_analysis_results(self, results: List[Dict], output_file: str = "job_match_analysis.json"):
        """Save analysis results to JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"💾 Analysis saved to {output_file}")
    
    def create_summary_report(self, results: List[Dict]) -> str:
        """Create a human-readable summary report."""
        
        if not results:
            return "No jobs analyzed."
        
        # Calculate statistics
        scores = [r.get('overall_score', 0) for r in results]
        avg_score = sum(scores) / len(scores)
        high_matches = len([s for s in scores if s >= 80])
        medium_matches = len([s for s in scores if 60 <= s < 80])
        
        report = f"""
🎯 RESUME-JOB MATCH ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 SUMMARY STATISTICS
• Total Jobs Analyzed: {len(results)}
• Average Match Score: {avg_score:.1f}/100
• High Matches (80+): {high_matches} jobs
• Medium Matches (60-79): {medium_matches} jobs

🔝 TOP 5 MATCHES
"""
        
        # Add top 5 matches
        for i, job in enumerate(results[:5], 1):
            score = job.get('overall_score', 0)
            title = job.get('job_title', 'No title')
            company = job.get('company', 'No company')
            priority = job.get('priority', 'UNKNOWN')
            
            report += f"\n{i}. {title} at {company}"
            report += f"\n   Score: {score}/100 | Priority: {priority}"
            report += f"\n   Job ID: {job.get('job_id', 'unknown')}"
            
            # Add top strengths
            strengths = job.get('strengths', [])[:2]
            if strengths:
                report += f"\n   Strengths: {', '.join(strengths)}"
            
            report += "\n"
        
        # Add priority recommendations
        high_priority = [j for j in results if j.get('priority') == 'HIGH']
        medium_priority = [j for j in results if j.get('priority') == 'MEDIUM']
        
        report += f"""
🎯 APPLICATION STRATEGY
• HIGH Priority: {len(high_priority)} jobs - Apply immediately
• MEDIUM Priority: {len(medium_priority)} jobs - Apply with tailored resume
• Review top gaps and missing keywords to improve future matches

📝 NEXT STEPS
1. Apply to HIGH priority jobs first
2. Tailor resume for top medium matches
3. Review missing keywords to update resume
4. Focus on addressing top skill gaps
"""
        
        return report
    
    def export_to_excel(self, results: List[Dict], output_file: str = "job_analysis.xlsx"):
        """Export results to Excel for easy filtering and sorting."""
        
        # Flatten results for Excel export
        excel_data = []
        
        for job in results:
            row = {
                'Job ID': job.get('job_id', ''),
                'Job Title': job.get('job_title', ''),
                'Company': job.get('company', ''),
                'Overall Score': job.get('overall_score', 0),
                'Technical Skills Score': job.get('technical_skills_score', 0),
                'Experience Score': job.get('experience_score', 0),
                'Domain Score': job.get('domain_score', 0),
                'Responsibilities Score': job.get('responsibilities_score', 0),
                'Priority': job.get('priority', ''),
                'Job URL': job.get('job_url', ''),
                'Top Strengths': ' | '.join(job.get('strengths', [])[:3]),
                'Main Gaps': ' | '.join(job.get('gaps', [])[:3]),
                'Missing Keywords': ' | '.join(job.get('missing_keywords', [])[:5]),
                'Key Recommendations': ' | '.join(job.get('recommendations', [])[:2])
            }
            excel_data.append(row)
        
        df = pd.DataFrame(excel_data)
        df.to_excel(output_file, index=False)
        print(f"📊 Excel report saved to {output_file}")

def convert_json_resume_to_text(resume_json: Dict) -> str:
    """Convert JSON resume format to readable text format."""
    
    text_parts = []
    
    # Personal Info
    personal = resume_json.get('personal_info', {})
    text_parts.append(f"Name: {personal.get('name', '')}")
    text_parts.append(f"Email: {personal.get('email', '')}")
    text_parts.append(f"Phone: {personal.get('phone', '')}")
    
    location = personal.get('location', {})
    if location:
        loc_str = f"{location.get('city', '')}, {location.get('state', '')} {location.get('country', '')}"
        text_parts.append(f"Location: {loc_str.strip()}")
    
    if personal.get('linkedin'):
        text_parts.append(f"LinkedIn: {personal.get('linkedin')}")
    
    text_parts.append("")  # Empty line
    
    # Education
    education = resume_json.get('education', [])
    if education:
        text_parts.append("EDUCATION:")
        for edu in education:
            text_parts.append(f"• {edu.get('degree', '')} - {edu.get('institution', '')}")
            if edu.get('gpa'):
                text_parts.append(f"  GPA: {edu.get('gpa')}")
        text_parts.append("")
    
    # Experience
    experience = resume_json.get('experience', [])
    if experience:
        text_parts.append("PROFESSIONAL EXPERIENCE:")
        for exp in experience:
            # Job header
            title = exp.get('position', '')
            company = exp.get('company', '')
            location = exp.get('location', '')
            start_date = exp.get('start_date', '')
            end_date = exp.get('end_date', '')
            
            text_parts.append(f"• {title} at {company}")
            text_parts.append(f"  {location} | {start_date} - {end_date}")
            
            # Responsibilities
            responsibilities = exp.get('responsibilities', [])
            for resp in responsibilities:
                text_parts.append(f"  - {resp}")
            
            # Technologies
            technologies = exp.get('technologies', [])
            if technologies:
                text_parts.append(f"  Technologies: {', '.join(technologies)}")
            
            text_parts.append("")  # Empty line between jobs
    
    # Skills
    skills = resume_json.get('skills', {})
    if skills:
        text_parts.append("TECHNICAL SKILLS:")
        
        # Programming languages
        prog_langs = skills.get('programming_languages', [])
        if prog_langs:
            text_parts.append(f"• Programming Languages: {', '.join(prog_langs)}")
        
        # Frameworks
        frameworks = skills.get('frameworks', [])
        if frameworks:
            text_parts.append(f"• Frameworks & Libraries: {', '.join(frameworks)}")
        
        # Tools
        tools = skills.get('tools', [])
        if tools:
            text_parts.append(f"• Tools & Technologies: {', '.join(tools)}")
        
        # Technical skills
        technical = skills.get('technical', [])
        if technical:
            text_parts.append(f"• Technical Expertise: {', '.join(technical)}")
        
        text_parts.append("")
    
    # Projects
    projects = resume_json.get('projects', [])
    if projects:
        text_parts.append("PROJECTS:")
        for project in projects:
            text_parts.append(f"• {project}")
        text_parts.append("")
    
    # Certifications
    certifications = resume_json.get('certifications', [])
    if certifications:
        text_parts.append("CERTIFICATIONS:")
        for cert in certifications:
            text_parts.append(f"• {cert}")
    
    return '\n'.join(text_parts)


def main():
    """Main function to run the analysis."""
    
    # Initialize matcher (make sure to set OPENAI_API_KEY environment variable)
    matcher = ResumeJobMatcher()
    
    # Load resume data
    resume_text = extract_text_from_pdf("Yutong-GenAI Engineer.pdf")
    
    if not resume_text.strip():
        print("❌ No resume text provided. Exiting.")
        return
    
    # Analyze all jobs
    jobs_file = "jobs_with_descriptions.json"
    
    if not os.path.exists(jobs_file):
        print(f"❌ Jobs file '{jobs_file}' not found. Please run the job collector first.")
        return
    
    # Run analysis
    results = matcher.analyze_all_jobs(jobs_file, resume_text)
    
    if not results:
        print("❌ No jobs could be analyzed.")
        return
    
    # Save results
    matcher.save_analysis_results(results)
    
    # Create and display summary report
    report = matcher.create_summary_report(results)
    print(report)
    
    # Save report to file
    with open("job_match_report.txt", "w", encoding='utf-8') as f:
        f.write(report)
    
    # Export to Excel (requires pandas and openpyxl)
    try:
        matcher.export_to_excel(results)
    except ImportError:
        print("💡 Install pandas and openpyxl to export Excel reports: pip install pandas openpyxl")
    
    print(f"\n✅ Analysis complete! Check these files:")
    print(f"   • job_match_analysis.json - Detailed analysis data")
    print(f"   • job_match_report.txt - Summary report")
    print(f"   • job_analysis.xlsx - Excel spreadsheet (if pandas installed)")

if __name__ == "__main__":
    main()