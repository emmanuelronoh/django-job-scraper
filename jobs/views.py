from django.shortcuts import render
from .models import Job
from .scraper import scrape_all_jobs  # updated scraper

def job_list(request):
    """
    View to display job listings.
    Scrapes jobs from Indeed and LinkedIn if 'scrape=true' is in the query params.
    """
    if request.GET.get("scrape") == "true":
        scrape_all_jobs()  # scrape both Indeed and LinkedIn

    jobs = Job.objects.all().order_by('-id')  # latest jobs first
    return render(request, "jobs/job_list.html", {"jobs": jobs})
