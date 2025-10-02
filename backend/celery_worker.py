# backend/celery_worker.py
from celery import Celery
import time

# Initialize Celery
# The first argument is the name of the current module.
# The `broker` argument specifies the URL of our Redis message broker.
# We use the hostname 'redis' which Docker Compose will resolve to the Redis container.
# The `backend` argument is where Celery stores task results.
celery_app = Celery(
    "worker",
    broker="redis://127.0.0.1:6379/0",
    backend="redis://127.0.0.1:6379/0"
)

# Optional: Configure Celery for better discoverability of tasks
celery_app.conf.update(
    task_track_started=True,
)

# Define a simple test task
@celery_app.task(name="create_test_task")
def create_test_task(x, y):
    """A simple task that adds two numbers together."""
    time.sleep(5)  # Simulate a long-running task
    return x + y