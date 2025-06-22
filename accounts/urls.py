from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Configuration du router pour les ViewSets (si nécessaire)
router = DefaultRouter()

app_name = 'accounts'

urlpatterns = [
    # Authentification JWT
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('logout-all/', views.LogoutAllDevicesView.as_view(), name='logout_all'),
    
    # Vérification et réinitialisation
    path('verify-email/<uuid:token>/', views.EmailVerificationView.as_view(), name='verify_email'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('reset-password/<uuid:token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Profil utilisateur 
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('preferences/', views.UserPreferencesView.as_view(), name='preferences'),
    
    # Gestion des appareils
    path('devices/', views.DeviceListView.as_view(), name='device_list'),
    path('devices/register/', views.DeviceRegistrationView.as_view(), name='device_register'),
    path('devices/<uuid:device_id>/deactivate/', views.DeviceDeactivateView.as_view(), name='device_deactivate'),
    path('devices/<uuid:device_id>/trust/', views.DeviceTrustView.as_view(), name='device_trust'),
    
    # Sécurité et statistiques
    path('login-attempts/', views.LoginAttemptsView.as_view(), name='login_attempts'),
    path('stats/', views.user_stats, name='user_stats'),
    
    # Gestion des utilisateurs (Admin)
    path('admin/users/', views.UserListView.as_view(), name='user-list'),
    path('admin/users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('admin/users/<int:pk>/activation/', views.UserActivationView.as_view(), name='user-activation'),
    path('admin/stats/', views.UserStatsView.as_view(), name='user-stats'),
    
    # Utilitaires
    path('choices/', views.UserChoicesView.as_view(), name='user-choices'),
]

# Optionnel: Ajouter des vues d'API documentation
