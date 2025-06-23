from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Configuration du router pour les ViewSets (si nécessaire)
router = DefaultRouter()

app_name = 'accounts'

# URLs pour les templates (pages web)
template_urlpatterns = [
    # Vérification et réinitialisation (Templates)
    path('verify-email/<uuid:token>/', views.EmailVerificationView.as_view(), name='verify_email'),
    path('password-reset/', views.PasswordResetRequestTemplateView.as_view(), name='password_reset_request'),
    path('password-reset/done/', views.PasswordResetDoneTemplateView.as_view(), name='password_reset_done'),
    path('reset-password/<uidb64>/<token>/', views.PasswordResetConfirmTemplateView.as_view(), name='password_reset_confirm'),
    path('reset-password/complete/', views.PasswordResetCompleteTemplateView.as_view(), name='password_reset_complete'),
    path('email-verified/', views.EmailVerificationSuccessView.as_view(), name='email_verification_success'),
]

# URLs pour l'API  
api_urlpatterns = [
    # Authentification JWT
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('logout-all/', views.LogoutAllDevicesView.as_view(), name='logout_all'),
    
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
    
    # Réinitialisation de mot de passe
    path('password-reset/', views.PasswordResetAPIView.as_view(), name='password_reset_api'),
]

# URLs combinées (pour compatibilité)
urlpatterns = api_urlpatterns + template_urlpatterns

# Optionnel: Ajouter des vues d'API documentation
