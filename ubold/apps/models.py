from django.db import models
# from ubold.users.models import User
from django.contrib.auth.models import User
from django.utils import timezone

from ubold.apps.constants import CATEGORY_CHOICES, CATEGORY_INFO


class Event(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=255, choices=CATEGORY_CHOICES, default=CATEGORY_INFO)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True)
    all_day = models.BooleanField(default=True)
    create_date = models.DateTimeField(default=timezone.now)

    def to_dict(self):
        e = {}
        e["pk"] = self.id
        e["title"] = self.title
        e["className"] = self.category
        e["start"] = self.start_date.isoformat()
        e["allDay"] = self.all_day
        e["create_date"] = self.create_date.isoformat()
        if self.end_date :
            e["end"] = self.end_date.isoformat()
        else:
            e["end"] = self.end_date
        return e
