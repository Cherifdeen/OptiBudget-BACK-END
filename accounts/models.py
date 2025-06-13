# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
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
    
    # SOLUTION : Ajouter related_name pour éviter les conflits
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',  # Évite le conflit
        related_query_name='custom_user',
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',  # Évite le conflit
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
        return self.username


class UserPreferences(models.Model):
    """Modèle pour les préférences utilisateur"""
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='preferences'
    )
    
    notifications_email = models.BooleanField(default=True)
    
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
        return f"Préférences de {self.user.username}"