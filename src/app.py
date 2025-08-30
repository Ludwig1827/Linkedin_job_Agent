from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import threading
import time
from datetime import datetime

# Import your existing modules
from resume_handling import extract_text_from_pdf, get_info_from_text
from generate_url import generate_linkedin_job_url
from get_jobs import LinkedInJobCollector, collect_linkedin_job_ids
from get_jd import load_collected_jobs, fetch_job_description, fetch_all_job_descriptions
from resume_job_matcher import ResumeJobMatcher
from dotenv import load_dotenv

load_dotenv(override=True)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables to track process status
process_status = {
    'status': 'idle',
    'step': '',
    'progress': 0,
    'message': '',
    'error': None,
    'results': None
}

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

@app.route('/')
def index():
    """Serve the main frontend page."""
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory('static', filename)

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current process status."""
    return jsonify(process_status)

@app.route('/api/upload-resume', methods=['POST'])
def upload_resume():
    """Upload and process resume PDF."""
    global process_status
    
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Save uploaded file
        filename = 'resume.pdf'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text from PDF
        process_status.update({
            'status': 'processing',
            'step': 'Extracting text from PDF',
            'progress': 25,
            'message': 'Processing your resume...'
        })
        
        resume_text = extract_text_from_pdf(filepath)
        
        # Extract structured information
        process_status.update({
            'step': 'Analyzing resume content',
            'progress': 50,
            'message': 'Extracting key information...'
        })
        
        resume_json = get_info_from_text(resume_text)
        
        # Save processed data
        with open('resume_data.json', 'w', encoding='utf-8') as f:
            json.dump({
                'text': resume_text,
                'structured': resume_json,
                'uploaded_at': datetime.now().isoformat()
            }, f, indent=2)
        
        process_status.update({
            'status': 'completed',
            'step': 'Resume processed',
            'progress': 100,
            'message': 'Resume uploaded and processed successfully!'
        })
        
        return jsonify({
            'success': True,
            'message': 'Resume processed successfully',
            'preview': {
                'name': resume_json.get('personal_info', {}).get('name', 'N/A'),
                'experience_count': len(resume_json.get('experience', [])),
                'education_count': len(resume_json.get('education', [])),
                'skills_count': len(resume_json.get('skills', {}).get('technical', []))
            }
        })
        
    except Exception as e:
        process_status.update({
            'status': 'error',
            'error': str(e),
            'message': f'Error processing resume: {str(e)}'
        })
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-url', methods=['POST'])
def generate_url():
    """Generate LinkedIn job search URL."""
    try:
        data = request.get_json()
        
        linkedin_url = generate_linkedin_job_url(
            keywords=data.get('keywords', 'AI Engineer'),
            geoId=data.get('geoId', '103644278'),
            location=data.get('location', 'United States'),
            distance=data.get('distance', 25),
            f_TPR=data.get('f_TPR', 'r86400'),
            sortBy=data.get('sortBy', 'R'),
            f_E=data.get('f_E', 4),
            f_SB2=data.get('f_SB2', 1)
        )
        
        return jsonify({
            'success': True,
            'url': linkedin_url,
            'parameters': data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/collect-jobs', methods=['POST'])
def collect_jobs():
    """Start job collection process in background."""
    global process_status
    
    try:
        data = request.get_json()
        linkedin_url = data.get('url')
        max_jobs = data.get('max_jobs', 10)
        
        if not linkedin_url:
            return jsonify({'error': 'LinkedIn URL is required'}), 400
        
        # Start background thread for job collection
        thread = threading.Thread(target=collect_jobs_background, args=(linkedin_url, max_jobs))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Job collection started. Please complete LinkedIn login in the browser window.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def collect_jobs_background(linkedin_url, max_jobs):
    """Background job collection process."""
    global process_status
    
    try:
        process_status.update({
            'status': 'processing',
            'step': 'Opening browser for LinkedIn login',
            'progress': 10,
            'message': 'Please complete LinkedIn login in the browser window...'
        })
        
        # Collect jobs
        jobs = collect_linkedin_job_ids(linkedin_url, max_jobs=max_jobs, headless=False)
        
        process_status.update({
            'step': 'Saving collected jobs',
            'progress': 70,
            'message': f'Collected {len(jobs)} jobs, saving data...'
        })
        
        # Save collected jobs
        with open("collected_jobs.json", "w") as f:
            json.dump(jobs, f, indent=4)
        
        process_status.update({
            'step': 'Fetching job descriptions',
            'progress': 80,
            'message': 'Fetching detailed job descriptions...'
        })
        
        # Fetch job descriptions
        jobs_data = load_collected_jobs("collected_jobs.json")
        jobs_with_descriptions = fetch_all_job_descriptions(
            jobs_data, 
            output_file="jobs_with_descriptions.json"
        )
        
        process_status.update({
            'status': 'completed',
            'step': 'Jobs collected successfully',
            'progress': 100,
            'message': f'Successfully collected {len(jobs_with_descriptions)} jobs with descriptions!',
            'results': {
                'job_count': len(jobs_with_descriptions),
                'jobs_file': 'jobs_with_descriptions.json'
            }
        })
        
    except Exception as e:
        process_status.update({
            'status': 'error',
            'error': str(e),
            'message': f'Error collecting jobs: {str(e)}'
        })

@app.route('/api/analyze-matches', methods=['POST'])
def analyze_matches():
    """Analyze resume against collected jobs."""
    global process_status
    
    try:
        # Check if resume and jobs data exist
        if not os.path.exists('resume_data.json'):
            return jsonify({'error': 'No resume data found. Please upload a resume first.'}), 400
        
        if not os.path.exists('jobs_with_descriptions.json'):
            return jsonify({'error': 'No job data found. Please collect jobs first.'}), 400
        
        # Start background analysis
        thread = threading.Thread(target=analyze_matches_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Analysis started. This may take a few minutes...'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def analyze_matches_background():
    """Background analysis process."""
    global process_status
    
    try:
        process_status.update({
            'status': 'processing',
            'step': 'Loading resume and job data',
            'progress': 10,
            'message': 'Preparing analysis...'
        })
        
        # Load resume data
        with open('resume_data.json', 'r', encoding='utf-8') as f:
            resume_data = json.load(f)
        resume_text = resume_data['text']
        
        process_status.update({
            'step': 'Initializing AI matcher',
            'progress': 20,
            'message': 'Setting up AI analysis...'
        })
        
        # Initialize matcher
        matcher = ResumeJobMatcher()
        
        process_status.update({
            'step': 'Analyzing job matches',
            'progress': 30,
            'message': 'Analyzing matches with AI...'
        })
        
        # Run analysis
        results = matcher.analyze_all_jobs("jobs_with_descriptions.json", resume_text)
        
        process_status.update({
            'step': 'Generating reports',
            'progress': 80,
            'message': 'Creating summary reports...'
        })
        
        # Save results
        with open("analysis_results.json", "w") as f:
            json.dump(results, f, indent=4)
        
        # Create summary report
        report = matcher.create_summary_report(results)
        with open("job_match_report.txt", "w", encoding='utf-8') as f:
            f.write(report)
        
        process_status.update({
            'status': 'completed',
            'step': 'Analysis complete',
            'progress': 100,
            'message': 'Job matching analysis completed successfully!',
            'results': {
                'total_jobs': len(results),
                'high_matches': len([r for r in results if r.get('overall_score', 0) >= 80]),
                'average_score': sum(r.get('overall_score', 0) for r in results) / len(results) if results else 0,
                'results_file': 'analysis_results.json',
                'report_file': 'job_match_report.txt'
            }
        })
        
    except Exception as e:
        process_status.update({
            'status': 'error',
            'error': str(e),
            'message': f'Error during analysis: {str(e)}'
        })

@app.route('/api/results', methods=['GET'])
def get_results():
    """Get analysis results."""
    try:
        if not os.path.exists('analysis_results.json'):
            return jsonify({'error': 'No analysis results found'}), 404
        
        with open('analysis_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Also load the summary report if it exists
        report = ""
        if os.path.exists('job_match_report.txt'):
            with open('job_match_report.txt', 'r', encoding='utf-8') as f:
                report = f.read()
        
        return jsonify({
            'success': True,
            'results': results,
            'report': report,
            'summary': {
                'total_jobs': len(results),
                'high_matches': len([r for r in results if r.get('overall_score', 0) >= 80]),
                'medium_matches': len([r for r in results if 60 <= r.get('overall_score', 0) < 80]),
                'average_score': sum(r.get('overall_score', 0) for r in results) / len(results) if results else 0
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_process():
    """Reset the entire process."""
    global process_status
    
    try:
        # Remove generated files
        files_to_remove = [
            'collected_jobs.json',
            'jobs_with_descriptions.json',
            'analysis_results.json',
            'job_match_report.txt',
            'resume_data.json'
        ]
        
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Reset status
        process_status = {
            'status': 'idle',
            'step': '',
            'progress': 0,
            'message': '',
            'error': None,
            'results': None
        }
        
        return jsonify({
            'success': True,
            'message': 'Process reset successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    """Download generated files."""
    allowed_files = [
        'analysis_results.json',
        'job_match_report.txt',
        'collected_jobs.json',
        'jobs_with_descriptions.json'
    ]
    
    if filename not in allowed_files:
        return jsonify({'error': 'File not allowed'}), 403
    
    if not os.path.exists(filename):
        return jsonify({'error': 'File not found'}), 404
    
    return send_from_directory('.', filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
