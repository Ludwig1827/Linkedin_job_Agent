# 🤖 AI Job Matcher - LinkedIn Resume Analyzer

An intelligent system that analyzes your resume against LinkedIn job postings using AI to find the best job matches and provide actionable insights for your job search.

## ✨ Features

- **📄 Resume Processing**: Upload PDF resumes and extract structured information using AI
- **🔍 Smart Job Collection**: Generate LinkedIn search URLs and collect job postings with Selenium
- **🤖 AI-Powered Matching**: Use OpenAI GPT models to analyze resume-job compatibility
- **📊 Detailed Analytics**: Get comprehensive match scores, strengths, gaps, and recommendations
- **🎯 Priority Ranking**: Jobs ranked by match quality with HIGH/MEDIUM/LOW priority labels
- **📱 Web Interface**: Clean, responsive React-based frontend with real-time progress tracking
- **📥 Export Options**: Download results as JSON reports and text summaries

## 🏗️ Architecture

```
├── src/
│   ├── app.py                 # Flask web application and API endpoints
│   ├── resume_handling.py     # PDF text extraction and AI parsing
│   ├── generate_url.py        # LinkedIn job search URL generation
│   ├── get_jobs.py           # Selenium-based job collection from LinkedIn
│   ├── get_jd.py             # Job description fetching and processing
│   ├── resume_job_matcher.py  # AI-powered resume-job matching engine
│   ├── main.py               # Command-line interface
│   └── test.py               # Environment testing
├── static/
│   └── index.html            # React-based web interface
└── uploads/                  # Temporary file storage
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Chrome browser (for Selenium)
- LinkedIn account

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-job-matcher
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   ```

4. **Install Chrome WebDriver**
   ```bash
   # Download ChromeDriver that matches your Chrome version
   # Place in PATH or project directory
   ```

### Usage

#### Web Interface (Recommended)

1. **Start the Flask server**
   ```bash
   python src/app.py
   ```

2. **Open your browser**
   ```
   http://localhost:5000
   ```

3. **Follow the 4-step process**:
   - 📄 Upload your resume PDF
   - 🔍 Configure job search parameters
   - 🤖 Run AI analysis
   - ✅ View results and download reports

#### Command Line Interface

```bash
# Run the complete pipeline
python src/main.py
```

## 📋 Requirements

```txt
flask
flask-cors
selenium
unstructured[pdf]
openai
python-dotenv
beautifulsoup4
requests
pandas
openpyxl
```

## ⚙️ Configuration

### Job Search Parameters

| Parameter | Description | Example Values |
|-----------|-------------|----------------|
| `keywords` | Job search terms | "AI Engineer", "Data Scientist" |
| `location` | Geographic location | "United States", "San Francisco" |
| `geoId` | LinkedIn location ID | 103644278 (US) |
| `f_E` | Experience level | 1=Internship, 4=Mid-Senior |
| `f_SB2` | Salary range | 1=$40k+, 4=$100k+ |
| `f_TPR` | Time period | r86400=24hrs, r604800=1week |
| `max_jobs` | Jobs to collect | 10, 25, 50 |

### Experience Levels
- `1` - Internship
- `2` - Entry Level  
- `3` - Associate
- `4` - Mid-Senior Level
- `5` - Director
- `6` - Executive

### Salary Ranges
- `1` - $40,000+
- `2` - $60,000+
- `3` - $80,000+
- `4` - $100,000+
- `5` - $120,000+
- `6` - $140,000+
- `7` - $160,000+
- `8` - $180,000+
- `9` - $200,000+

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload-resume` | POST | Upload and process resume PDF |
| `/api/generate-url` | POST | Generate LinkedIn job search URL |
| `/api/collect-jobs` | POST | Start background job collection |
| `/api/analyze-matches` | POST | Begin AI analysis of resume vs jobs |
| `/api/status` | GET | Get current process status |
| `/api/results` | GET | Retrieve analysis results |
| `/api/reset` | POST | Reset entire process |
| `/api/download/<file>` | GET | Download generated reports |

## 📊 Analysis Output

### Match Scores (0-100)
- **Overall Score**: Comprehensive compatibility rating
- **Technical Skills**: Programming languages, frameworks, tools alignment
- **Experience Level**: Years of experience and seniority match
- **Domain Experience**: Industry and domain expertise fit
- **Responsibilities**: Past role duties vs job requirements

### Priority Levels
- **🔴 HIGH**: 80+ overall score - Apply immediately
- **🟡 MEDIUM**: 60-79 overall score - Tailor resume and apply
- **⚫ LOW**: <60 overall score - Consider skill development

### Detailed Insights
- ✅ **Strengths**: Top matching qualifications
- ❌ **Gaps**: Missing requirements and skills
- 🔑 **Missing Keywords**: Important terms to add to resume
- 💡 **Recommendations**: Actionable improvement suggestions

## 📁 Generated Files

- `resume_data.json` - Structured resume information
- `collected_jobs.json` - Raw job data from LinkedIn
- `jobs_with_descriptions.json` - Jobs with full descriptions
- `analysis_results.json` - Detailed match analysis
- `job_match_report.txt` - Human-readable summary
- `linkedin_cookies.json` - Saved session (auto-generated)

## 🔒 LinkedIn Authentication

The system supports multiple authentication methods:

1. **Manual Login (Recommended)**: Browser opens for manual login
2. **Cookie-based**: Reuse saved session cookies
3. **Automatic**: Use credentials (not recommended for security)

```python
# Manual login (most reliable)
jobs = collect_linkedin_job_ids(search_url, headless=False)

# With saved cookies
collector = LinkedInJobCollector()
collector.ensure_logged_in(cookies_file="linkedin_cookies.json")
```

## ⚠️ Important Notes

### Rate Limiting & Ethics
- Respectful scraping with delays between requests
- Manual login reduces detection risk
- Follows LinkedIn's robots.txt guidelines
- Use reasonable job collection limits (≤50)

### Data Privacy
- All processing happens locally
- Resume data stored temporarily
- No data sent to third parties (except OpenAI API)
- Generated files contain sensitive information

### LinkedIn Terms of Service
- This tool is for personal job searching only
- Respect LinkedIn's Terms of Service
- Don't use for commercial data harvesting
- Be mindful of API rate limits

## 🐛 Troubleshooting

### Common Issues

**Chrome Driver Issues**
```bash
# Download matching ChromeDriver version
# https://chromedriver.chromium.org/
```

**LinkedIn Login Problems**
- Use manual login for best results
- Complete any 2FA challenges
- Clear cookies if authentication fails

**OpenAI API Errors**
- Verify API key in .env file
- Check API quota and billing
- Model availability (gpt-4o-mini)

**PDF Processing Errors**
- Ensure PDF is not password-protected
- Try different PDF if text extraction fails
- Check file size limits (16MB max)

### Debug Mode
```python
# Enable Flask debug mode
app.run(debug=True, port=5000)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI** - GPT models for resume and job analysis
- **Unstructured** - PDF text extraction
- **Selenium** - Web automation for LinkedIn
- **Flask** - Web framework
- **React** - Frontend interface

## 🔮 Future Enhancements

- [ ] Support for multiple resume formats (DOCX, TXT)
- [ ] Integration with other job boards (Indeed, Glassdoor)
- [ ] Resume optimization suggestions
- [ ] Interview preparation based on job requirements
- [ ] Email alerts for new matching jobs
- [ ] Chrome extension for easier job analysis
- [ ] Export to ATS-friendly formats

---

**⭐ Star this repository if it helps with your job search!**

For questions, issues, or feature requests, please create an issue in the repository.
