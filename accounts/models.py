# models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'email est obligatoire')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    # Remplacer username par email
    username = None
    email = models.EmailField(unique=True, verbose_name='Adresse email')
    
    # Champs de sécurité
    is_email_verified = models.BooleanField(default=False, verbose_name='Email vérifié')
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    failed_login_attempts = models.IntegerField(default=0, verbose_name='Tentatives de connexion échouées')
    account_locked_until = models.DateTimeField(null=True, blank=True, verbose_name='Compte verrouillé jusqu\'à')
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='Dernière IP de connexion')
    
    # Vos champs personnalisés
    phone = models.CharField(max_length=20, blank=True, null=True)
    nom_entr = models.CharField(max_length=255, blank=True, null=True)
    date_naiss = models.DateField(blank=True, null=True)
    img_profil = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    TYPE_COMPTE = [
        ('particulier', 'Particulier'),
        ('entreprise', 'Entreprise'),
    ]
    compte = models.CharField(max_length=20, choices=TYPE_COMPTE, default='particulier')
    
    profession = models.CharField(max_length=255, blank=True, null=True)
    
    PAYS = [
        ('FR', 'France'),
        ('SN', 'Sénégal'),
        ('BJ', 'Bénin'),
        ('CI', 'Côte d\'Ivoire'),
        # Ajoutez d'autres pays
    ]
    pays = models.CharField(max_length=2, choices=PAYS, blank=True, null=True)
    
    DEVISES = [
        ('EUR', 'Euro'),
        ('XOF', 'Franc CFA'),
        ('USD', 'Dollar US'),
    ]
    devise = models.CharField(max_length=3, choices=DEVISES, default='EUR')
    
    LANGUES = [
        ('fr', 'Français'),
        ('en', 'English'),
    ]
    langue = models.CharField(max_length=2, choices=LANGUES, default='fr')
    
    statut_compte = models.BooleanField(default=True)
    
    # Champs de date
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name='Date d\'inscription')
    last_activity = models.DateTimeField(auto_now=True, verbose_name='Dernière activité')
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',  
        related_query_name='custom_user',
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',  
        related_query_name='custom_user',
    )
    
    class Meta:
        db_table = 'custom_users'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
    
    def get_full_name(self):
        """Retourne le nom complet de l'utilisateur"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def __str__(self):
        return self.email
    
    def is_account_locked(self):
        """Vérifie si le compte est verrouillé"""
        if self.account_locked_until and self.account_locked_until > timezone.now():
            return True
        return False
    
    def lock_account(self, hours=24):
        """Verrouille le compte pour une durée donnée"""
        self.account_locked_until = timezone.now() + timedelta(hours=hours)
        self.save()
    
    def unlock_account(self):
        """Déverrouille le compte"""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save()
    
    def increment_failed_attempts(self):
        """Incrémente le nombre de tentatives échouées"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 10:
            self.lock_account(24)
        self.save()

class UserDevice(models.Model):
    """Modèle pour gérer les appareils connectés"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='devices')
    device_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    device_name = models.CharField(max_length=255, verbose_name='Nom de l\'appareil')
    device_type = models.CharField(max_length=50, verbose_name='Type d\'appareil')
    browser = models.CharField(max_length=100, blank=True, verbose_name='Navigateur')
    os = models.CharField(max_length=100, blank=True, verbose_name='Système d\'exploitation')
    ip_address = models.GenericIPAddressField(verbose_name='Adresse IP')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    is_active = models.BooleanField(default=True, verbose_name='Appareil actif')
    is_trusted = models.BooleanField(default=False, verbose_name='Appareil de confiance')
    last_used = models.DateTimeField(auto_now=True, verbose_name='Dernière utilisation')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    
    class Meta:
        db_table = 'user_devices'
        verbose_name = 'Appareil utilisateur'
        verbose_name_plural = 'Appareils utilisateur'
        unique_together = ['user', 'device_id']
    
    def __str__(self):
        return f"{self.device_name} - {self.user.email}"

class LoginAttempt(models.Model):
    """Modèle pour tracer les tentatives de connexion"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='login_attempts')
    ip_address = models.GenericIPAddressField(verbose_name='Adresse IP')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    success = models.BooleanField(default=False, verbose_name='Connexion réussie')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Horodatage')
    device = models.ForeignKey(UserDevice, on_delete=models.SET_NULL, null=True, blank=True, related_name='login_attempts')
    
    class Meta:
        db_table = 'login_attempts'
        verbose_name = 'Tentative de connexion'
        verbose_name_plural = 'Tentatives de connexion'
        ordering = ['-timestamp']
    
    def __str__(self):
        status = "Réussie" if self.success else "Échouée"
        return f"{self.user.email} - {status} - {self.timestamp}"

class UserPreferences(models.Model):
    """Modèle pour les préférences utilisateur"""
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='preferences'
    )
    
    notifications_email = models.BooleanField(default=True)
    notifications_push = models.BooleanField(default=True)
    two_factor_auth = models.BooleanField(default=False, verbose_name='Authentification à deux facteurs')
    
    THEMES = [
        ('light', 'Clair'),
        ('dark', 'Sombre'),
        ('auto', 'Automatique'),
    ]
    theme = models.CharField(max_length=10, choices=THEMES, default='auto')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_preferences'
        verbose_name = 'Préférence utilisateur'
        verbose_name_plural = 'Préférences utilisateur'
    
    def __str__(self):
        return f"Préférences de {self.user.email}"