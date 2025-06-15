from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Configuration du router pour les ViewSets (si nécessaire)
router = DefaultRouter()

urlpatterns = [
    # Authentification
    path('auth/register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('auth/login/', views.UserLoginView.as_view(), name='user-login'),
    path('auth/logout/', views.UserLogoutView.as_view(), name='user-logout'),
    
    # Profil utilisateur
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/preferences/', views.UserPreferencesView.as_view(), name='user-preferences'),
    path('profile/change-password/', views.PasswordChangeView.as_view(), name='change-password'),
    path('profile/upload-image/', views.upload_profile_image, name='upload-profile-image'),
    path('profile/delete-image/', views.delete_profile_image, name='delete-profile-image'),
    
    # Réinitialisation de mot de passe
    path('auth/password-reset/', views.password_reset_request, name='password-reset-request'),
    path('auth/password-reset-confirm/<str:uidb64>/<str:token>/', 
         views.password_reset_confirm, name='password-reset-confirm'),
    path('verify-password/',views.PasswordVerificationView.as_view(), name='verify-password'),
    
    # Vérification de disponibilité
    path('check/username/', views.check_username_availability, name='check-username'),
    path('check/email/', views.check_email_availability, name='check-email'),
    
    # Gestion des utilisateurs (Admin)
    path('admin/users/', views.UserListView.as_view(), name='user-list'),
    path('admin/users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('admin/users/<int:pk>/activation/', views.UserActivationView.as_view(), name='user-activation'),
    path('admin/stats/', views.UserStatsView.as_view(), name='user-stats'),
    
    # Utilitaires
    path('choices/', views.UserChoicesView.as_view(), name='user-choices'),
    

]

# Optionnel: Ajouter des vues d'API documentation
