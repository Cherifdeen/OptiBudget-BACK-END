import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Optibudget.settings')

app = Celery('Optibudget')

# Configure le broker Redis
app.config_from_object('django.conf:settings', namespace='CELERY')

# Recherche automatique des tâches dans les applications installées dans les fichiers 
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'clean-expired-tokens': {
        'task': 'tasks.tokenExpireManager.clean_expired_tokens',
        'schedule': crontab(hour=2, minute=0),  # Tous les jours à 2h
    },
}

