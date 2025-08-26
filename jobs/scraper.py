from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from .models import Job
import time
from datetime import datetime, timedelta
import re

def get_text_or_default(element, selectors, default="N/A"):
    """Try multiple selectors, return first found text."""
    for selector in selectors:
        try:
            elems = element.find_elements(By.CSS_SELECTOR, selector)
            if elems:
                text = elems[0].text.strip()
                if text and text not in ['', ' ', '·']:  # Filter out empty or separator text
                    return text
        except Exception:
            continue
    return default

def parse_relative_date(date_string):
    """Parse relative dates like 'Just now', '1 day ago', etc."""
    if not date_string or date_string == "N/A":
        return datetime.now().date()
    
    date_string = date_string.lower()
    
    # Handle "just now", "today", etc.
    if 'just now' in date_string or 'today' in date_string:
        return datetime.now().date()
    
    # Handle "X days ago"
    days_match = re.search(r'(\d+)\s+days? ago', date_string)
    if days_match:
        days_ago = int(days_match.group(1))
        return (datetime.now() - timedelta(days=days_ago)).date()
    
    # Handle "X hours ago"
    hours_match = re.search(r'(\d+)\s+hours? ago', date_string)
    if hours_match:
        return datetime.now().date()
    
    # Handle "X weeks ago"
    weeks_match = re.search(r'(\d+)\s+weeks? ago', date_string)
    if weeks_match:
        weeks_ago = int(weeks_match.group(1))
        return (datetime.now() - timedelta(weeks=weeks_ago)).date()
    
    return datetime.now().date()

def scrape_indeed():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.7204.168 Safari/537.36"
    )

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.indeed.com/jobs?q=python+developer&l=remote")

    # Scroll to load more jobs
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_pause = 2
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    try:
        job_cards = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".job_seen_beacon, .cardOutline, .jobsearch-SerpJobCard"))
        )
        print(f"Found {len(job_cards)} Indeed job cards")

        for card in job_cards:
            try:
                # Better selectors for Indeed
                title = get_text_or_default(card, [
                    "h2.jobTitle span", 
                    "h2 a span", 
                    ".jobTitle span",
                    "[data-testid='jobTitle']",
                    "h2"
                ])
                
                company = get_text_or_default(card, [
                    ".companyName", 
                    ".company",
                    "[data-testid='company-name']",
                    ".companyOverviewLink"
                ])
                
                location = get_text_or_default(card, [
                    ".companyLocation", 
                    ".location",
                    "[data-testid='text-location']",
                    ".locationAccessibility"
                ])
                
                # Get date posted
                date_posted_text = get_text_or_default(card, [
                    ".date", 
                    ".result-link-bar-container span",
                    ".jobsearch-SerpJobCard-footer span",
                    ".posted-since"
                ], "N/A")
                
                date_posted = parse_relative_date(date_posted_text)
                
                link_elem = card.find_elements(By.CSS_SELECTOR, "h2 a, a.jobTitle, a[data-jk]")
                link = link_elem[0].get_attribute("href") if link_elem else None

                # Debug output
                print(f"Indeed - Title: '{title}', Company: '{company}', Location: '{location}', Date: '{date_posted_text}'")

                if link and not Job.objects.filter(link=link).exists():
                    Job.objects.create(
                        title=title,
                        company=company,
                        location=location,
                        link=link,
                        source="Indeed",
                        date_posted=date_posted
                    )
                    print(f"Saved Indeed job: {title} at {company}")

            except Exception as e:
                print(f"Error scraping Indeed card: {e}")

    except TimeoutException:
        print("Error: Indeed job cards did not load in time.")
    finally:
        driver.quit()

def scrape_linkedin():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.7204.168 Safari/537.36"
    )

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.linkedin.com/jobs/search/?keywords=Python%20Developer&location=Remote")

    try:
        # Wait for the actual job results to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search__results-list, .scaffold-layout__list-container"))
        )
        
        # Scroll to load more jobs - more scrolls for LinkedIn
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            # Try to click "See more jobs" if it exists
            try:
                see_more = driver.find_elements(By.CSS_SELECTOR, "button.infinite-scroller__show-more-button")
                if see_more:
                    see_more[0].click()
                    time.sleep(2)
            except:
                pass

        # More specific selectors for LinkedIn job cards
        job_cards = driver.find_elements(By.CSS_SELECTOR, 
            ".jobs-search-results__list-item, " +
            "li.jobs-search-results__list-item, " +
            ".job-card-container, " +
            ".job-card-list, " +
            "[data-entity-urn^='urn:li:jobPosting:']"
        )
        print(f"Found {len(job_cards)} potential LinkedIn job elements")

        valid_jobs_count = 0
        
        for card in job_cards:
            try:
                # More specific selectors for LinkedIn
                title = get_text_or_default(card, [
                    "h3.base-search-card__title",
                    ".job-card-list__title",
                    "h3.job-card-title",
                    ".artdeco-entity-lockup__title",
                    "h3"
                ])
                
                company = get_text_or_default(card, [
                    "h4.base-search-card__subtitle",
                    ".job-card-container__company-name",
                    ".artdeco-entity-lockup__subtitle",
                    "h4.job-card-company-name",
                    "h4"
                ])
                
                location = get_text_or_default(card, [
                    ".job-card-container__metadata-item",
                    ".job-search-card__location",
                    ".job-card-location",
                    ".artdeco-entity-lockup__caption",
                    ".job-card-container__metadata-wrapper"
                ])
                
                # Get date posted
                date_posted_text = get_text_or_default(card, [
                    "time",
                    ".job-search-card__listdate",
                    ".job-card-container__metadata-item--last-modified",
                    ".posted-time-ago__text",
                    ".job-card-container__metadata-item:nth-child(2)"
                ], "N/A")
                
                date_posted = parse_relative_date(date_posted_text)
                
                link_elem = card.find_elements(By.CSS_SELECTOR, 
                    "a.base-card__full-link, " +
                    "a.job-card-container__link, " +
                    "a.job-card-list__title, " +
                    "a[href*='/jobs/view/']"
                )
                link = link_elem[0].get_attribute("href") if link_elem else None

                # Skip if essential data is missing or looks like an ad
                if (title == "N/A" and company == "N/A") or not link:
                    continue
                
                if any(x in title.lower() for x in ['promoted', 'sponsored', 'advertisement']):
                    continue
                
                if any(x in company.lower() for x in ['promoted', 'sponsored']):
                    continue

                # Debug output
                print(f"LinkedIn - Title: '{title}', Company: '{company}', Location: '{location}', Date: '{date_posted_text}'")

                if link and not Job.objects.filter(link=link).exists():
                    Job.objects.create(
                        title=title,
                        company=company,
                        location=location,
                        link=link,
                        source="LinkedIn",
                        date_posted=date_posted
                    )
                    print(f"Saved LinkedIn job: {title} at {company}")
                    valid_jobs_count += 1

            except Exception as e:
                print(f"Error scraping LinkedIn card: {e}")
        
        print(f"Successfully processed {valid_jobs_count} valid LinkedIn jobs")

    except Exception as e:
        print(f"Error finding LinkedIn jobs: {e}")
    finally:
        driver.quit()

def scrape_all_jobs():
    print("Starting Indeed scrape...")
    scrape_indeed()
    print("Starting LinkedIn scrape...")
    scrape_linkedin()
    print("Scraping completed!")