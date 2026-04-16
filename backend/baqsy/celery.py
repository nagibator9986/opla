import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baqsy.settings.dev")

app = Celery("baqsy")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

from celery.schedules import crontab  # noqa: E402

app.conf.beat_schedule = {
    "remind-incomplete-submissions": {
        "task": "submissions.remind_incomplete",
        "schedule": crontab(hour="*/6"),  # every 6 hours
    },
}
