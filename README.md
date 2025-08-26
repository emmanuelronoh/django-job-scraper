# Django Job Scraper

A Django-based web application that scrapes and displays job listings from various job boards such as Indeed.  
The dashboard allows you to view job title, company, location, posting date, expiration date, and source.

## Features
- Scrape jobs from Indeed (and easily extendable to more sources).
- Store job details in a Django model.
- Display jobs in a clean dashboard with links to the original posting.
- Track posting date and expiration date.
- Avoid duplicates using unique job links.

## Tech Stack
- **Backend:** Django
- **Frontend:** HTML, CSS (Django templates)
- **Database:** SQLite (default, can switch to PostgreSQL/MySQL)
- **Scraping:** BeautifulSoup / Requests

## Installation
```bash
git clone https://github.com/your-username/django-job-scraper.git
cd django-job-scraper
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
