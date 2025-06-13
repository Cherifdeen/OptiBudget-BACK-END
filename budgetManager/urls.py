from django.urls import path
from . import views

app_name = 'budget'

urlpatterns = [
    # URLs pour Budget
    path('budgets/', views.BudgetViewSet.as_view({'get': 'list', 'post': 'create'}), name='budget-list'),
    path('budgets/<int:pk>/', views.BudgetViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='budget-detail'),
    path('budgets/<int:pk>/categories/', views.BudgetViewSet.as_view({'get': 'categories'}), name='budget-categories'),
    path('budgets/<int:pk>/depenses/', views.BudgetViewSet.as_view({'get': 'depenses'}), name='budget-depenses'),
    path('budgets/<int:pk>/resume/', views.BudgetViewSet.as_view({'get': 'resume'}), name='budget-resume'),

    # URLs pour CategorieDepense
    path('categories-depense/', views.CategorieDepenseViewSet.as_view({'get': 'list', 'post': 'create'}), name='categoriedepense-list'),
    path('categories-depense/<int:pk>/', views.CategorieDepenseViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='categoriedepense-detail'),
    path('categories-depense/<int:pk>/depenses/', views.CategorieDepenseViewSet.as_view({'get': 'depenses'}), name='categoriedepense-depenses'),

    # URLs pour Depense
    path('depenses/', views.DepenseViewSet.as_view({'get': 'list', 'post': 'create'}), name='depense-list'),
    path('depenses/<int:pk>/', views.DepenseViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='depense-detail'),
    path('depenses/statistiques/', views.DepenseViewSet.as_view({'get': 'statistiques'}), name='depense-statistiques'),

    # URLs pour Entree
    path('entrees/', views.EntreeViewSet.as_view({'get': 'list', 'post': 'create'}), name='entree-list'),
    path('entrees/<int:pk>/', views.EntreeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='entree-detail'),
    path('entrees/statistiques/', views.EntreeViewSet.as_view({'get': 'statistiques'}), name='entree-statistiques'),

    # URLs pour Notification
    path('notifications/', views.NotificationViewSet.as_view({'get': 'list', 'post': 'create'}), name='notification-list'),
    path('notifications/<int:pk>/', views.NotificationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='notification-detail'),
    path('notifications/non-lues/', views.NotificationViewSet.as_view({'get': 'non_lues'}), name='notification-non-lues'),
    path('notifications/<int:pk>/marquer-lue/', views.NotificationViewSet.as_view({'post': 'marquer_lue'}), name='notification-marquer-lue'),
    path('notifications/marquer-toutes-lues/', views.NotificationViewSet.as_view({'post': 'marquer_toutes_lues'}), name='notification-marquer-toutes-lues'),

    # URLs pour Conseil
    path('conseils/', views.ConseilViewSet.as_view({'get': 'list', 'post': 'create'}), name='conseil-list'),
    path('conseils/<int:pk>/', views.ConseilViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='conseil-detail'),
    path('conseils/recents/', views.ConseilViewSet.as_view({'get': 'recents'}), name='conseil-recents'),

    # URLs pour Employe (comptes entreprise)
    path('employes/', views.EmployeViewSet.as_view({'get': 'list', 'post': 'create'}), name='employe-list'),
    path('employes/<int:pk>/', views.EmployeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='employe-detail'),
    path('employes/<int:pk>/paiements/', views.EmployeViewSet.as_view({'get': 'paiements'}), name='employe-paiements'),
    path('employes/actifs/', views.EmployeViewSet.as_view({'get': 'actifs'}), name='employe-actifs'),

    # URLs pour PaiementEmploye
    path('paiements-employes/', views.PaiementEmployeViewSet.as_view({'get': 'list', 'post': 'create'}), name='paiementemploye-list'),
    path('paiements-employes/<int:pk>/', views.PaiementEmployeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='paiementemploye-detail'),
    path('paiements-employes/statistiques/', views.PaiementEmployeViewSet.as_view({'get': 'statistiques'}), name='paiementemploye-statistiques'),

    # URLs pour MontantSalaire
    path('montants-salaire/', views.MontantSalaireViewSet.as_view({'get': 'list', 'post': 'create'}), name='montantsalaire-list'),
    path('montants-salaire/<int:pk>/', views.MontantSalaireViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='montantsalaire-detail'),
    path('montants-salaire/calculer/', views.MontantSalaireViewSet.as_view({'post': 'calculer'}), name='montantsalaire-calculer'),
]