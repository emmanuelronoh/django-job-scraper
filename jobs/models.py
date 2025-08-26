from django.db import models
from django.utils import timezone
from datetime import timedelta

def default_expiry():
    return timezone.now().date() + timedelta(days=30)

class Job(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    link = models.URLField(unique=True)
    source = models.CharField(max_length=50, default="Indeed")
    date_posted = models.DateField(default=timezone.now)
    expiry_date = models.DateField(default=default_expiry)  # Fixed

    def __str__(self):
        return f"{self.title} - {self.company} ({self.source})"
