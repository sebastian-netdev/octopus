import os
import time

from celery import Celery
from kombu import Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Octopus.settings')

app = Celery('Octopus',broker='redis://localhost:6379/0')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"
app.conf.task_default_queue = "default"



app.conf.task_queues = (
    Queue("default", routing_key="task.#"),
    Queue("Kaufland", routing_key="Kaufland.task.#"),
    Queue("sync", routing_key="sync.#"),
)

task_default_exchange = 'tasks'
task_default_exchange_type = 'topic'
task_default_routing_key = 'task.default'
task_routes = {
        'Kaufland.tasks.*': {
            'queue': 'Kaufland',
            'routing_key': 'Kaufland.task.#',
        },
}
app.control.inspect()

app.conf.task_default_routing_key = "task.default"

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
