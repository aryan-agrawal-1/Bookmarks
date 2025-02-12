from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Create a Celery instance
app = Celery('config')

# Load configuration from Django settings, using the CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from installed Django apps
app.autodiscover_tasks()

# Test task
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
