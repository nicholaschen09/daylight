import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("energy_management")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "simulate-telemetry": {
        "task": "core.tasks.simulate_telemetry",
        "schedule": 60.0,
    },
}
