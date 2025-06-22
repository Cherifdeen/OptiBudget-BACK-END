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
    
}


app.conf.beat_schedule = {
    # Marquer les budgets expirés tous les jours à minuit
    'marquer-budgets-expires': {
        'task': 'votre_app.tasks.marquer_budgets_expires',
        'schedule': crontab(hour=0, minute=0),  # Tous les jours à minuit
    },
    
    # Générer les statistiques hebdomadaires tous les dimanches à 23h
    'statistiques-hebdomadaires': {
        'task': 'budgetManager.tasks.generer_statistiques_hebdomadaires',
        'schedule': crontab(hour=23, minute=0, day_of_week=0),  # Dimanche à 23h
    },
    
    # Générer les bilans finaux des budgets expirés tous les jours à 1h
    'bilans-budgets-expires': {
        'task': 'budgetManager.tasks.generer_statistiques_budgets_expires',
        'schedule': crontab(hour=1, minute=0),  # Tous les jours à 1h
    },
    
    # Rapport quotidien tous les jours à 8h
    'rapport-quotidien': {
        'task': 'budgetManager.tasks.rapport_quotidien_budgets',
        'schedule': crontab(hour=8, minute=0),  # Tous les jours à 8h
    },
    
    # Nettoyer les anciennes notifications tous les dimanches à 2h
    'nettoyer-notifications': {
        'task': 'budgetManager.tasks.nettoyer_anciennes_notifications',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Dimanche à 2h
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


