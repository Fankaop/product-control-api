from celery import Celery
from core.config import settings
from celery.schedules import crontab

celery_app = Celery(
    "product_control",
    broker=settings.celery_broker_url,  
    backend=settings.celery_result_backend,      
    include=[        
        "tasks.aggregation",
        "tasks.reports",
        "tasks.imports",
        "tasks.exports",
        "tasks.scheduled",
        "tasks.webhooks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,   
    result_expires=3600,   
)

celery_app.conf.beat_schedule = {
    "auto-close-expired-batches": {
        "task": "tasks.scheduled.auto_close_expired_batches",
        "schedule": crontab(hour=1, minute=0),
    },
    "cleanup-old-files": {
        "task": "tasks.scheduled.cleanup_old_files",
        "schedule": crontab(hour=2, minute=0),
    },
    "update-statistics": {
        "task": "tasks.scheduled.update_cached_statistics",
        "schedule": crontab(minute="*/5"),
    },
    "retry-failed-webhooks": {
        "task": "tasks.scheduled.retry_failed_webhooks",
        "schedule": crontab(minute="*/15"),
    },
}