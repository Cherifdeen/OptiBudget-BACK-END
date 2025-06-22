from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'budget'

# Configuration du router principal
router = DefaultRouter()
router.register(r'budgets', views.BudgetViewSet, basename='budget')
router.register(r'categories-depense', views.CategorieDepenseViewSet, basename='categorie-depense')
router.register(r'depenses', views.DepenseViewSet, basename='depense')
router.register(r'entrees', views.EntreeViewSet, basename='entree')
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'conseils', views.ConseilViewSet, basename='conseil')
router.register(r'employes', views.EmployeViewSet, basename='employe')
router.register(r'paiements-employes', views.PaiementEmployeViewSet, basename='paiement-employe')
router.register(r'montants-salaire', views.MontantSalaireViewSet, basename='montant-salaire')

urlpatterns = [
    # Inclusion des URLs générées par le router
    path('', include(router.urls)),
    
    # URLs personnalisées susceptibles d'être perturbées - conservées en path
    # Statistiques globales et rapports
    path('categories-depense/stats-globales/', 
         views.CategorieDepenseViewSet.as_view({'get': 'stats_globales'}), 
         name='categoriedepense-stats-globales'),
    
    path('paiements-employes/paiement-global/', 
         views.PaiementEmployeViewSet.as_view({'post': 'paiement_global'}), 
         name='paiement-global'),
    
    path('paiements-employes/preview-paiement-global/', 
         views.PaiementEmployeViewSet.as_view({'get': 'preview_paiement_global'}), 
         name='preview-paiement-global'),
    
    path('paiements-employes/statistiques/', 
         views.PaiementEmployeViewSet.as_view({'get': 'statistiques'}), 
         name='paiements-statistiques'),
    
    path('paiements-employes/par-employe/', 
         views.PaiementEmployeViewSet.as_view({'get': 'par_employe'}), 
         name='paiements-par-employe'),
    
    path('montants-salaire/calculer/', 
         views.MontantSalaireViewSet.as_view({'post': 'calculer'}), 
         name='montantsalaire-calculer'),
    
    path('notifications/non-lues/', 
         views.NotificationViewSet.as_view({'get': 'non_lues'}), 
         name='notification-non-lues'),
    
    path('notifications/marquer-toutes-lues/', 
         views.NotificationViewSet.as_view({'post': 'marquer_toutes_lues'}), 
         name='notification-marquer-toutes-lues'),
    
    path('employes/actifs/', 
         views.EmployeViewSet.as_view({'get': 'actifs'}), 
         name='employe-actifs'),
    
    path('employes/par_statut/<str:statut>/', 
         views.EmployeViewSet.as_view({'get': 'par_statut'}), 
         name='employe-par-statut'),
    
    path('conseils/recents/', 
         views.ConseilViewSet.as_view({'get': 'recents'}), 
         name='conseil-recents'),
    
    # URLs de statistiques personnalisées (fonctions de vues)
    path('budgets/<uuid:budget_id>/statistiques/', views.budget_statistics, name='budget-statistics'),
    path('budgets/statistiques-globales/', views.all_budgets_statistics, name='all-budgets-statistics'),
    path('categories/<uuid:category_id>/statistiques/', views.category_statistics, name='category-statistics'),
    path('rapport-financier-global/', views.global_financial_report, name='global-financial-report'),
    
    # Endpoint de test des conseils
    path('test-conseils/', views.test_conseils_par_type, name='test-conseils-par-type'),
]


