# apps.py
from django.apps import AppConfig


class BudgetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'budgetManager'  # Remplacez par le nom de votre application
    
    def ready(self):
        # Importer les signaux pour qu'ils soient enregistrés
        import budgetManager.signals  # Remplacez par le nom de votre application