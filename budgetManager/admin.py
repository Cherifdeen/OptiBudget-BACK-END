# budgetManager/admin.py
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from .models import Budget,CategorieDepense,Depense,Entree,Employe,Notification,Conseil,PaiementEmploye,MontantSalaire

admin.site.register(Budget)
admin.site.register(CategorieDepense)
admin.site.register(Depense)
admin.site.register(Entree)
admin.site.register(Employe)
admin.site.register(Notification)
admin.site.register(Conseil)
admin.site.register(PaiementEmploye)
admin.site.register(MontantSalaire)

# Importez vos tâches
from budgetManager.tasks import (
    marquer_budgets_expires,
    generer_statistiques_hebdomadaires,
    generer_statistiques_budgets_expires,
    rapport_quotidien_budgets,
    nettoyer_anciennes_notifications
)

class TaskAdmin:
    """Classe pour ajouter l'interface de gestion des tâches à l'admin"""
    
    def run_tasks_view(self, request):
        """Vue pour l'interface de gestion des tâches"""
        if request.method == 'POST':
            task_name = request.POST.get('task')
            
            tasks = {
                'all': 'Toutes les tâches',
                'marquer_expires': marquer_budgets_expires,
                'stats_hebdo': generer_statistiques_hebdomadaires,
                'bilans_expires': generer_statistiques_budgets_expires,
                'rapport_quotidien': rapport_quotidien_budgets,
                'nettoyer_notifs': nettoyer_anciennes_notifications,
            }
            
            try:
                if task_name == 'all':
                    # Exécuter toutes les tâches
                    task_results = {}
                    for name, task in tasks.items():
                        if name != 'all' and callable(task):
                            result = task.delay()
                            task_results[name] = result.id
                    
                    messages.success(request, f'Toutes les tâches ont été lancées! IDs: {task_results}')
                    
                elif task_name in tasks and callable(tasks[task_name]):
                    # Exécuter une tâche spécifique
                    result = tasks[task_name].delay()
                    messages.success(request, f'Tâche {task_name} lancée avec succès! ID: {result.id}')
                    
                else:
                    messages.error(request, f'Tâche {task_name} non trouvée')
                    
            except Exception as e:
                messages.error(request, f'Erreur lors du lancement de la tâche: {str(e)}')
            
            return redirect('admin:run_tasks')
        
        # Préparer le contexte pour le template
        context = {
            'title': 'Exécution des tâches de budget',
            'tasks': [
                ('all', 'Toutes les tâches'),
                ('marquer_expires', 'Marquer budgets expirés'),
                ('stats_hebdo', 'Statistiques hebdomadaires'),
                ('bilans_expires', 'Bilans budgets expirés'),
                ('rapport_quotidien', 'Rapport quotidien'),
                ('nettoyer_notifs', 'Nettoyer notifications'),
            ],
            'opts': {'app_label': 'budgetManager', 'model_name': 'tasks'},
            'has_change_permission': True,
        }
        
        return render(request, 'admin/run_tasks.html', context)

    @require_POST
    def run_task_api(self, request):
        """API pour exécuter les tâches via AJAX"""
        task_name = request.POST.get('task')
        
        tasks = {
            'marquer_expires': marquer_budgets_expires,
            'stats_hebdo': generer_statistiques_hebdomadaires,
            'bilans_expires': generer_statistiques_budgets_expires,
            'rapport_quotidien': rapport_quotidien_budgets,
            'nettoyer_notifs': nettoyer_anciennes_notifications,
        }
        
        try:
            if task_name == 'all':
                results = {}
                for name, task in tasks.items():
                    result = task.delay()
                    results[name] = result.id
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Toutes les tâches ont été lancées',
                    'task_ids': results
                })
            
            elif task_name in tasks:
                result = tasks[task_name].delay()
                return JsonResponse({
                    'status': 'success',
                    'message': f'Tâche {task_name} lancée',
                    'task_id': result.id
                })
            
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Tâche non trouvée',
                    'available_tasks': list(tasks.keys())
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Erreur: {str(e)}'
            })


# SOLUTION CORRIGÉE : Hériter de AdminSite au lieu de modifier get_urls
class CustomAdminSite(admin.AdminSite):
    """Site d'administration personnalisé avec gestion des tâches"""
    
    def get_urls(self):
        # Récupérer les URLs par défaut de l'admin
        urls = super().get_urls()
        
        # Créer une instance de TaskAdmin
        task_admin = TaskAdmin()
        
        # Ajouter nos URLs personnalisées
        custom_urls = [
            path('run-tasks/', 
                 self.admin_view(task_admin.run_tasks_view), 
                 name='run_tasks'),
            path('run-task-api/', 
                 self.admin_view(task_admin.run_task_api), 
                 name='run_task_api'),
        ]
        
        return custom_urls + urls

# Créer une instance de notre site d'admin personnalisé
admin_site = CustomAdminSite(name='custom_admin')





# admin_site.register(VotreModel)