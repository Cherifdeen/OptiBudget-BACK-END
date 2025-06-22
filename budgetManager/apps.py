# apps.py
from django.apps import AppConfig


class BudgetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'budgetManager'
    
    def ready(self):
        
        import budgetManager.signals  