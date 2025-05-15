from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379/0')

app.conf.update(
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=300,
)
