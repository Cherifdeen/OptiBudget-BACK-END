# 📱 Application Accounts - SMARTBUDGET

## 🎯 Vue d'ensemble

L'application `accounts` gère l'authentification et la gestion des utilisateurs pour SMARTBUDGET. Elle utilise un système d'authentification JWT moderne avec gestion des appareils et sécurité renforcée.

## 🔐 Fonctionnalités principales

### Authentification JWT
- **Email + mot de passe** (plus d'username)
- Tokens d'accès et de rafraîchissement
- Blacklisting automatique des tokens
- Durée de vie configurable

### Sécurité
- Verrouillage automatique après 10 échecs (24h)
- Traçage des tentatives de connexion
- Vérification d'email obligatoire
- Gestion des appareils connectés

### Gestion des appareils
- Enregistrement automatique des appareils
- Détection intelligente (navigateur, OS, type)
- Marquage de confiance
- Déconnexion à distance

## 📁 Structure des fichiers

```
accounts/
├── __init__.py
├── admin.py              # Configuration admin Django
├── apps.py               # Configuration de l'application
├── middleware.py         # Middlewares personnalisés
├── models.py             # Modèles de données
├── serializers.py        # Sérialiseurs DRF
├── urls.py               # Configuration des URLs
├── views.py              # Vues API
├── migrations/           # Migrations de base de données
└── README.md            # Ce fichier
```

## 🗄️ Modèles de données

### CustomUser
```python
class CustomUser(AbstractUser):
    # Champs principaux
    email = models.EmailField(unique=True)
    username = None  # Supprimé, email utilisé à la place
    
    # Sécurité
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Métadonnées
    date_joined = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Champs personnalisés existants
    phone, nom_entr, date_naiss, img_profil, compte, 
    profession, pays, devise, langue, statut_compte
```

### UserDevice
```python
class UserDevice(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    device_id = models.UUIDField(default=uuid.uuid4, unique=True)
    device_name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=50)  # mobile, tablet, desktop
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_trusted = models.BooleanField(default=False)
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### LoginAttempt
```python
class LoginAttempt(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    device = models.ForeignKey(UserDevice, on_delete=models.SET_NULL, null=True)
```

### UserPreferences
```python
class UserPreferences(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    notifications_email = models.BooleanField(default=True)
    notifications_push = models.BooleanField(default=True)
    two_factor_auth = models.BooleanField(default=False)
    theme = models.CharField(max_length=10, choices=THEMES, default='auto')
```

## 🔧 Sérialiseurs

### CustomTokenObtainPairSerializer
```python
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Sérialiseur personnalisé pour l'obtention de tokens JWT
    - Vérifie si le compte est verrouillé
    - Incrémente les tentatives échouées
    - Enregistre les tentatives de connexion
    - Réinitialise les tentatives en cas de succès
    """
```

### UserRegistrationSerializer
```python
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'inscription d'un nouvel utilisateur
    - Validation des mots de passe
    - Création automatique des préférences
    - Envoi d'email de vérification
    """
```

### UserDeviceSerializer
```python
class UserDeviceSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la gestion des appareils
    - Lecture seule pour device_id, ip_address, last_used, created_at
    """
```

## 🌐 Vues API

### Authentification
```python
class CustomTokenObtainPairView(TokenObtainPairView):
    """Vue personnalisée pour l'obtention de tokens JWT"""

class UserRegistrationView(generics.CreateAPIView):
    """Vue pour l'inscription d'un nouvel utilisateur"""

class LogoutView(APIView):
    """Vue pour la déconnexion"""

class LogoutAllDevicesView(APIView):
    """Vue pour déconnecter tous les appareils"""
```

### Vérification et réinitialisation
```python
class EmailVerificationView(APIView):
    """Vue pour la vérification d'email"""

class PasswordResetRequestView(APIView):
    """Vue pour demander une réinitialisation de mot de passe"""

class PasswordResetConfirmView(APIView):
    """Vue pour confirmer la réinitialisation de mot de passe"""
```

### Profil et préférences
```python
class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vue pour le profil utilisateur"""

class ChangePasswordView(APIView):
    """Vue pour changer le mot de passe"""

class UserPreferencesView(generics.RetrieveUpdateAPIView):
    """Vue pour les préférences utilisateur"""
```

### Gestion des appareils
```python
class DeviceListView(generics.ListAPIView):
    """Vue pour lister les appareils de l'utilisateur"""

class DeviceRegistrationView(generics.CreateAPIView):
    """Vue pour enregistrer un nouvel appareil"""

class DeviceDeactivateView(APIView):
    """Vue pour désactiver un appareil"""

class DeviceTrustView(APIView):
    """Vue pour marquer un appareil comme de confiance"""
```

### Sécurité et statistiques
```python
class LoginAttemptsView(generics.ListAPIView):
    """Vue pour lister les tentatives de connexion"""

@api_view(['GET'])
def user_stats(request):
    """Vue pour les statistiques utilisateur"""
```

## 🛣️ URLs

```python
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
```

## 🔧 Middlewares

### DeviceDetectionMiddleware
```python
class DeviceDetectionMiddleware(MiddlewareMixin):
    """
    Middleware pour détecter automatiquement les appareils
    - Analyse le User-Agent
    - Extrait les informations de l'appareil
    - Stocke les données dans request.device_info
    """
```

### SecurityMiddleware
```python
class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware pour la sécurité et la gestion des tentatives de connexion
    - Vérifie les tentatives par IP
    - Récupère l'adresse IP réelle du client
    """
```

### ActivityTrackingMiddleware
```python
class ActivityTrackingMiddleware(MiddlewareMixin):
    """
    Middleware pour suivre l'activité des utilisateurs
    - Met à jour last_activity à chaque requête
    """
```

## 📧 Templates d'emails

### email_verification.html
- Template pour la vérification d'email
- Design responsive avec gradient
- Bouton de vérification
- Lien de secours

### password_reset.html
- Template pour la réinitialisation de mot de passe
- Avertissements de sécurité
- Instructions détaillées

## ⚙️ Configuration requise

### Dépendances
```bash
pip install djangorestframework-simplejwt
pip install django-cors-headers
pip install user-agents
pip install python-decouple
```

### Variables d'environnement (.env)
```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
GEMINI_API_KEY=your-gemini-key
EMAIL_HOST=your-smtp-host
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=SMARTBUDGET@site.com
```

### Configuration Django (settings.py)
```python
INSTALLED_APPS = [
    # ...
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'accounts.middleware.DeviceDetectionMiddleware',
    'accounts.middleware.SecurityMiddleware',
    'accounts.middleware.ActivityTrackingMiddleware',
    # ...
]
```

## 🔒 Sécurité

### Verrouillage de compte
- Après 10 tentatives échouées, le compte est verrouillé 24h
- Les tentatives sont tracées avec IP et User-Agent
- Réinitialisation automatique en cas de connexion réussie

### Gestion des tokens
- Tokens d'accès : 60 minutes
- Tokens de rafraîchissement : 7 jours
- Rotation automatique des tokens
- Blacklisting des tokens expirés

### Vérification d'email
- Token UUID unique pour chaque utilisateur
- Expiration automatique après utilisation
- Templates d'email sécurisés

## 📊 Utilisation

### Inscription
```bash
POST /api/accounts/register/
{
    "email": "user@example.com",
    "password": "securepassword123",
    "password_confirm": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
}
```

### Connexion
```bash
POST /api/accounts/login/
{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

### Rafraîchissement de token
```bash
POST /api/accounts/token/refresh/
{
    "refresh": "your-refresh-token"
}
```

### Utilisation du token
```bash
GET /api/accounts/profile/
Authorization: Bearer your-access-token
```

## 🚀 Déploiement

1. **Migrations** : Appliquer les migrations
```bash
python manage.py migrate
```

2. **Variables d'environnement** : Configurer le fichier .env

3. **Email** : Configurer SMTP pour les emails

4. **CORS** : Configurer les origines autorisées

5. **Sécurité** : Changer SECRET_KEY en production

## 📝 Notes importantes

- L'application utilise l'email comme identifiant principal
- Les utilisateurs existants sont migrés automatiquement
- Les appareils sont détectés automatiquement
- La sécurité est renforcée avec traçage complet
- Les templates d'emails sont responsives et professionnels

## 🤝 Contribution

Pour contribuer à cette application :
1. Suivre les conventions Django
2. Ajouter des tests pour les nouvelles fonctionnalités
3. Documenter les changements
4. Respecter les bonnes pratiques de sécurité 