import time
import re
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import List, Dict, Optional
import urllib.parse

class LinkedInJobCollector:
    def __init__(self, headless: bool = True, wait_time: int = 10, login_required: bool = True):
        """
        Initialize the LinkedIn job collector.
        
        Args:
            headless: Run browser in headless mode
            wait_time: Maximum wait time for elements to load
            login_required: Whether to handle LinkedIn login
        """
        self.wait_time = wait_time
        self.login_required = login_required
        self.driver = self._setup_driver(headless)
        self.collected_jobs = []
        self.is_logged_in = False
        
    def _setup_driver(self, headless: bool) -> webdriver.Chrome:
        """Setup Chrome driver with appropriate options."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent to appear more human-like
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def manual_login_prompt(self):
        """Prompt user to manually log in to LinkedIn."""
        print("\n" + "="*60)
        print("LINKEDIN LOGIN REQUIRED")
        print("="*60)
        print("1. The browser window will open to LinkedIn's login page")
        print("2. Please log in manually with your LinkedIn credentials")
        print("3. Complete any 2FA or security challenges if prompted")
        print("4. Navigate to any LinkedIn page to confirm you're logged in")
        print("5. Return to this terminal and press ENTER when ready")
        print("="*60)
        
        # Navigate to LinkedIn login
        self.driver.get("https://www.linkedin.com/login")
        
        # Wait for user to login manually
        input("\nPress ENTER after you have successfully logged in to LinkedIn...")
        
        # Verify login by checking if we're redirected
        try:
            # Check if we're on a LinkedIn page (not login page)
            current_url = self.driver.current_url
            if "linkedin.com/login" not in current_url or self.driver.find_elements(By.CSS_SELECTOR, "[data-control-name='nav.settings']"):
                self.is_logged_in = True
                print("✅ Login successful!")
                return True
            else:
                print("❌ Login verification failed. Please ensure you're logged in.")
                return False
        except Exception as e:
            print(f"⚠️  Could not verify login status: {e}")
            # Assume login worked if no error
            self.is_logged_in = True
            return True
    
    def auto_login(self, email: str, password: str):
        """
        Attempt automatic login (use with caution - may trigger security measures).
        
        Args:
            email: LinkedIn email
            password: LinkedIn password
            
        Returns:
            bool: Success status
        """
        try:
            print("Attempting automatic login...")
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for login form
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Fill in credentials
            email_field = self.driver.find_element(By.ID, "username")
            password_field = self.driver.find_element(By.ID, "password")
            
            email_field.clear()
            email_field.send_keys(email)
            
            password_field.clear()
            password_field.send_keys(password)
            
            # Submit form
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait and check for successful login or challenges
            time.sleep(5)
            
            current_url = self.driver.current_url
            
            # Check if we need to handle 2FA or security challenge
            if "challenge" in current_url or "checkpoint" in current_url:
                print("🔐 Security challenge detected. Please complete manually...")
                input("Press ENTER after completing the security challenge...")
            
            # Verify login
            if "feed" in current_url or "linkedin.com/in/" in current_url:
                self.is_logged_in = True
                print("✅ Automatic login successful!")
                return True
            else:
                print("❌ Automatic login failed. Falling back to manual login.")
                return False
                
        except Exception as e:
            print(f"❌ Automatic login error: {e}")
            return False
    
    def use_cookies_login(self, cookies_file: str = "linkedin_cookies.json"):
        """
        Login using saved cookies from a previous session.
        
        Args:
            cookies_file: Path to saved cookies JSON file
        """
        try:
            with open(cookies_file, 'r') as f:
                cookies = json.load(f)
            
            # Go to LinkedIn first
            self.driver.get("https://www.linkedin.com")
            
            # Add cookies
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Failed to add cookie: {e}")
            
            # Refresh to apply cookies
            self.driver.refresh()
            time.sleep(3)
            
            # Check if logged in
            current_url = self.driver.current_url
            if "feed" in current_url or self.driver.find_elements(By.CSS_SELECTOR, "[data-control-name='nav.settings']"):
                self.is_logged_in = True
                print("✅ Cookie login successful!")
                return True
            else:
                print("❌ Cookie login failed - cookies may be expired")
                return False
                
        except FileNotFoundError:
            print(f"❌ Cookie file {cookies_file} not found")
            return False
        except Exception as e:
            print(f"❌ Cookie login error: {e}")
            return False
    
    def save_cookies(self, cookies_file: str = "linkedin_cookies.json"):
        """Save current session cookies for future use."""
        try:
            cookies = self.driver.get_cookies()
            with open(cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            print(f"✅ Cookies saved to {cookies_file}")
        except Exception as e:
            print(f"❌ Failed to save cookies: {e}")
    
    def ensure_logged_in(self, email: str = None, password: str = None, cookies_file: str = None):
        """
        Ensure user is logged in using multiple methods.
        
        Args:
            email: LinkedIn email (for auto login)
            password: LinkedIn password (for auto login)
            cookies_file: Path to saved cookies file
        """
        if self.is_logged_in:
            return True
        
        print("LinkedIn authentication required...")
        
        # Method 1: Try cookies if provided
        if cookies_file:
            print("Trying cookie-based login...")
            if self.use_cookies_login(cookies_file):
                return True
        
        # Method 2: Try automatic login if credentials provided
        if email and password:
            print("Trying automatic login...")
            if self.auto_login(email, password):
                # Save cookies for future use
                self.save_cookies()
                return True
        
        # Method 3: Manual login (most reliable)
        print("Using manual login...")
        if self.manual_login_prompt():
            # Save cookies for future use
            self.save_cookies()
            return True
        
        return False
        
    def extract_job_id_from_url(self, url: str) -> Optional[str]:
        """Extract currentJobId from LinkedIn URL."""
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        if 'currentJobId' in query_params:
            return query_params['currentJobId'][0]
        return None
    
    def wait_for_page_load(self):
        """Wait for the page to fully load."""
        try:
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-job-id]"))
            )
            time.sleep(2)  # Additional wait for dynamic content
        except TimeoutException:
            print("Warning: Page load timeout")
    
    def get_job_ids_from_page(self) -> List[str]:
        """Extract all job IDs from the current page."""
        job_ids = []
        
        try:
            # Method 1: Look for data-job-id attributes
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-job-id]")
            for element in job_elements:
                job_id = element.get_attribute("data-job-id")
                if job_id and job_id not in job_ids:
                    job_ids.append(job_id)
            
            # Method 2: Extract from href attributes
            if not job_ids:
                job_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/jobs/view/']")
                for link in job_links:
                    href = link.get_attribute("href")
                    if href:
                        match = re.search(r'/jobs/view/(\d+)', href)
                        if match and match.group(1) not in job_ids:
                            job_ids.append(match.group(1))
            
            # Method 3: Extract from current URL
            current_job_id = self.extract_job_id_from_url(self.driver.current_url)
            if current_job_id and current_job_id not in job_ids:
                job_ids.append(current_job_id)
                
        except Exception as e:
            print(f"Error extracting job IDs: {e}")
        
        return job_ids
    
    def click_next_job(self) -> bool:
        """Click on the next job in the list. Returns True if successful."""
        try:
            # Find all job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, 
                "[data-job-id], .job-card-container, .jobs-search-results__list-item")
            
            if len(job_cards) <= 1:
                return False
            
            # Find currently selected job
            current_job_id = self.extract_job_id_from_url(self.driver.current_url)
            current_index = -1
            
            for i, card in enumerate(job_cards):
                job_id = card.get_attribute("data-job-id")
                if job_id == current_job_id:
                    current_index = i
                    break
            
            # Click next job
            next_index = current_index + 1
            if next_index < len(job_cards):
                job_cards[next_index].click()
                time.sleep(2)  # Wait for page to update
                return True
                
        except Exception as e:
            print(f"Error clicking next job: {e}")
        
        return False
    
    def scroll_to_load_more_jobs(self):
        """Scroll down to load more jobs."""
        try:
            # Scroll to bottom of job list
            job_list = self.driver.find_element(By.CSS_SELECTOR, 
                ".jobs-search-results__list, .jobs-search__results-list")
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", job_list)
            time.sleep(2)
            
            # Look for "Show more jobs" button
            try:
                show_more_btn = self.driver.find_element(By.CSS_SELECTOR, 
                    "button[aria-label*='more'], .jobs-search-results__pagination button")
                if show_more_btn.is_enabled():
                    show_more_btn.click()
                    time.sleep(3)
                    return True
            except NoSuchElementException:
                pass
                
        except Exception as e:
            print(f"Error scrolling: {e}")
        
        return False
    
    def collect_job_ids_from_search(self, search_url: str, max_jobs: int = 100, 
                                   email: str = None, password: str = None) -> List[Dict]:
        """
        Collect job IDs from a LinkedIn search URL.
        
        Args:
            search_url: LinkedIn job search URL
            max_jobs: Maximum number of jobs to collect
            email: LinkedIn email (optional, for auto-login)
            password: LinkedIn password (optional, for auto-login)
            
        Returns:
            List of job dictionaries with ID, title, company, etc.
        """
        print(f"Starting job collection from: {search_url}")
        
        # Ensure we're logged in
        if not self.ensure_logged_in(email, password, "linkedin_cookies.json"):
            print("❌ Failed to log in to LinkedIn. Cannot proceed.")
            return []
        
        # Navigate to search URL
        self.driver.get(search_url)
        self.wait_for_page_load()
        
        collected_jobs = []
        seen_job_ids = set()
        
        while len(collected_jobs) < max_jobs:
            # Get current page job IDs
            current_job_ids = self.get_job_ids_from_page()
            
            # Process each job ID
            for job_id in current_job_ids:
                if job_id not in seen_job_ids and len(collected_jobs) < max_jobs:
                    job_info = self.get_job_info(job_id)
                    if job_info:
                        collected_jobs.append(job_info)
                        seen_job_ids.add(job_id)
                        print(f"Collected job {len(collected_jobs)}: {job_id} - {job_info.get('title', 'N/A')}")
            
            # Try to load more jobs
            if not self.scroll_to_load_more_jobs():
                # Try clicking next job to get more from pagination
                if not self.click_next_job():
                    print("No more jobs to load")
                    break
            
            # Prevent infinite loops
            time.sleep(1)
        
        self.collected_jobs.extend(collected_jobs)
        return collected_jobs
    
    def get_job_info(self, job_id: str) -> Optional[Dict]:
        """Get basic job information for a job ID."""
        try:
            # Navigate to specific job if not already there
            current_job_id = self.extract_job_id_from_url(self.driver.current_url)
            if current_job_id != job_id:
                # Click on the job card with this ID
                job_element = self.driver.find_element(By.CSS_SELECTOR, f"[data-job-id='{job_id}']")
                job_element.click()
                time.sleep(2)
            
            # Extract job information
            job_info = {
                'job_id': job_id,
                'url': f"https://www.linkedin.com/jobs/view/{job_id}",
                'timestamp': time.time()
            }
            
            # Try to get job title
            try:
                title_element = self.driver.find_element(By.CSS_SELECTOR, 
                    "h1.job-title, .job-details-jobs-unified-top-card__job-title")
                job_info['title'] = title_element.text.strip()
            except:
                job_info['title'] = None
            
            # Try to get company name
            try:
                company_element = self.driver.find_element(By.CSS_SELECTOR, 
                    ".job-details-jobs-unified-top-card__company-name, .job-card__company-name")
                job_info['company'] = company_element.text.strip()
            except:
                job_info['company'] = None
            
            # Try to get location
            try:
                location_element = self.driver.find_element(By.CSS_SELECTOR, 
                    ".job-details-jobs-unified-top-card__bullet, .job-card__location")
                job_info['location'] = location_element.text.strip()
            except:
                job_info['location'] = None
            
            return job_info
            
        except Exception as e:
            print(f"Error getting job info for {job_id}: {e}")
            return {
                'job_id': job_id,
                'url': f"https://www.linkedin.com/jobs/view/{job_id}",
                'title': None,
                'company': None,
                'location': None,
                'timestamp': time.time()
            }
    
    def save_jobs_to_file(self, filename: str = "linkedin_jobs.json"):
        """Save collected jobs to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.collected_jobs, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(self.collected_jobs)} jobs to {filename}")
    
    def close(self):
        """Close the browser driver."""
        if self.driver:
            self.driver.quit()

# Helper function for easy usage
def collect_linkedin_job_ids(search_url: str, max_jobs: int = 50, headless: bool = True,
                           email: str = None, password: str = None) -> List[Dict]:
    """
    Simple function to collect LinkedIn job IDs from a search URL.
    
    Args:
        search_url: LinkedIn job search URL
        max_jobs: Maximum number of jobs to collect
        headless: Run browser in headless mode
        email: LinkedIn email (optional)
        password: LinkedIn password (optional)
        
    Returns:
        List of job dictionaries
    """
    collector = LinkedInJobCollector(headless=headless)
    
    try:
        jobs = collector.collect_job_ids_from_search(search_url, max_jobs, email, password)
        return jobs
    finally:
        collector.close()

# Example usage
if __name__ == "__main__":
    # Your LinkedIn search URL
    search_url = "https://www.linkedin.com/jobs/search/?currentJobId=4266063414&distance=25&f_E=4&f_SB2=1&f_TPR=r86400&geoId=103644278&keywords=AI%20Engineer&location=United%20States&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true&sortBy=R"
    
    print("=== LinkedIn Job ID Collection with Authentication ===")
    
    # Option 1: Manual login (most reliable)
    print("\n📝 OPTION 1: Manual Login (Recommended)")
    print("The browser will open for you to login manually")
    jobs = collect_linkedin_job_ids(search_url, max_jobs=10, headless=False)
    
    # Option 2: With credentials (use carefully)
    # print("\n🔐 OPTION 2: Automatic Login")
    # jobs = collect_linkedin_job_ids(
    #     search_url, 
    #     max_jobs=10, 
    #     headless=False,
    #     email="your_email@example.com",
    #     password="your_password"
    # )
    
    # Option 3: Advanced usage with cookie management
    # print("\n🍪 OPTION 3: Using Saved Session")
    # collector = LinkedInJobCollector(headless=False)
    # if collector.ensure_logged_in(cookies_file="linkedin_cookies.json"):
    #     jobs = collector.collect_job_ids_from_search(search_url, max_jobs=10)
    # collector.close()
    
    # Display results
    if jobs:
        print(f"\n✅ Successfully collected {len(jobs)} jobs!")
        print("\n=== Job Summary ===")
        for i, job in enumerate(jobs, 1):
            print(f"{i}. Job ID: {job['job_id']}")
            print(f"   Title: {job.get('title', 'N/A')}")
            print(f"   Company: {job.get('company', 'N/A')}")
            print(f"   URL: {job['url']}")
            print()
        
        # Save to file
        with open("collected_jobs.json", "w") as f:
            json.dump(jobs, f, indent=2)
        print(f"💾 Jobs saved to collected_jobs.json")
        
        # Extract just the job IDs
        job_ids = [job['job_id'] for job in jobs]
        print(f"\n🆔 Job IDs: {job_ids}")
    else:
        print("❌ No jobs collected. Please check authentication and try again.")
        
    print("\n💡 Tips for next time:")
    print("- Use the saved cookies file for faster login")
    print("- Run with headless=False to see what's happening")
    print("- Check linkedin_cookies.json was created for future use")