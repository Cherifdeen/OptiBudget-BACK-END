from django.db import models
from django.conf import settings  # Ajout de l'import pour settings
import uuid
from django.core.exceptions import ValidationError

# Create your models here.


class Budget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100,unique=True)
    montant = models.FloatField(default=0.0)
    montant_initial = models.FloatField(default=0.0)
    date_fin = models.DateField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Correction ici
    actif = models.BooleanField(default=True)
    D = [
        ('D', 'Durée determiner'),
        ('I', 'Durée non determiner'),
    ]
    type_budget = models.CharField(max_length=3, choices=D, default='D')
    bilan_fait = models.BooleanField(default=False)


class CategorieDepense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100,unique=True)
    description = models.TextField(null=True, blank=True)
    montant = models.FloatField(default=0.0)
    montant_initial = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id_budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Correction ici


class Depense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    montant = models.FloatField(default=0.0)
    TYPES = [
        ('DP', 'depense'),
        ('SL', 'salaires'),
    ]
    type_depense = models.CharField(max_length=30, choices=TYPES, default='DP')
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id_budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    id_cat_depense = models.ForeignKey(CategorieDepense, null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Correction ici


class Entree(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    montant = models.FloatField(default=0.0)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id_budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Correction ici
    def save(self, *args, **kwargs):
        # Vérifier que l'utilisateur associé au budget a un compte entreprise
        if self.id_budget.user.compte != 'entreprise':
            raise ValidationError("Seuls les comptes entreprise peuvent créer des entrées")
        super().save(*args, **kwargs)


class Employe(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField(null=True, blank=True)
    adresse = models.TextField(null=True, blank=True)
    telephone = models.CharField(max_length=100)
    email = models.EmailField(null=False, blank=True)
    
    TYPE_EMPLOYE_CHOICES = [
        ('DIR', 'Direction'),
        ('CAD', 'Cadre'),
        ('EMP', 'Employé'),
        ('OUV', 'Ouvrier'),
        ('CON', 'Consultant/Freelance'),
        ('STA', 'Stagiaire/Alternant'),
        ('INT', 'Intérimaire'),
        ('AUT', 'Autre'),  # Correction de 'Antre' -> 'Autre'
    ]
    type_employe = models.CharField(max_length=3, choices=TYPE_EMPLOYE_CHOICES, default='AUT')
    poste = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Correction ici
    prise_service = models.DateTimeField(null=True, blank=True)
    img_profil = models.ImageField(
        upload_to='profiles/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Image de profil"
    )
    
    ACT = [
        ('ES', 'En service'),
        ('EC', 'En congé'),
        ('ER', 'Retraité'),  # Correction de 'Retaité' -> 'Retraité'
        ('LC', 'Licencié'),
        ('HS', 'Hors service'),
        ('DM', 'Démissionné'),  # Correction de 'Demissionné' -> 'Démissionné'
    ]
    actif = models.CharField(max_length=3, choices=ACT, default='ES')


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.TextField()
    TYPES=[
        ('INFO','Information'),
        ('WARNING','attention'),
        ('SUCCESS','succes'),
        ('ERROR','erreur'),
        ('LOG','Evenement'),
        
    ]
    type_notification=models.TextField(null=True,blank=True,default='INFO',choices=TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE)  # Correction ici
    viewed = models.BooleanField(default=False)


class Conseil(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_budget = models.ForeignKey(Budget, on_delete=models.CASCADE, null=True, blank=True)
    nom = models.TextField(default='conseil')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Correction ici
    viewed = models.BooleanField(default=False)


class PaiementEmploye(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_employe = models.ForeignKey(Employe, on_delete=models.CASCADE)
    montant = models.FloatField(default=0.0)
    date_paiement = models.DateTimeField(auto_now_add=True)
    type_paiement = models.CharField(max_length=50, choices=[('SALAIRE', 'Salaire')])
    description = models.TextField(blank=True, null=True)
    id_budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Correction ici
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class MontantSalaire(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Correction ici
    salaire_direction = models.FloatField(default=0.0)
    bonus_direction = models.FloatField(default=0.0)
    indemnite_direction = models.FloatField(default=0.0)
    avance_direction = models.FloatField(default=0.0)
    salaire_cadre = models.FloatField(default=0.0)
    bonus_cadre = models.FloatField(default=0.0)
    indemnite_cadre = models.FloatField(default=0.0)
    avance_cadre = models.FloatField(default=0.0)
    salaire_employe = models.FloatField(default=0.0)
    bonus_employe = models.FloatField(default=0.0)
    indemnite_employe = models.FloatField(default=0.0)
    avance_employe = models.FloatField(default=0.0)
    salaire_ouvrier = models.FloatField(default=0.0)
    bonus_ouvrier = models.FloatField(default=0.0)
    indemnite_ouvrier = models.FloatField(default=0.0)
    avance_ouvrier = models.FloatField(default=0.0)
    salaire_cf = models.FloatField(default=0.0)
    bonus_cf = models.FloatField(default=0.0)
    indemnite_cf = models.FloatField(default=0.0)
    avance_cf = models.FloatField(default=0.0)
    salaire_stagiaire = models.FloatField(default=0.0)
    bonus_stagiaire = models.FloatField(default=0.0)
    indemnite_stagiaire = models.FloatField(default=0.0)
    avance_stagiaire = models.FloatField(default=0.0)
    salaire_intermediaire = models.FloatField(default=0.0)
    bonus_intermediaire = models.FloatField(default=0.0)
    indemnite_intermediaire = models.FloatField(default=0.0)
    avance_intermediaire = models.FloatField(default=0.0)
    salaire_autre = models.FloatField(default=0.0)
    bonus_autre = models.FloatField(default=0.0)
    indemnite_autre = models.FloatField(default=0.0)
    avance_autre = models.FloatField(default=0.0)

    salaire_hebdomadaire = models.FloatField(default=0.0)
    salaire_horaire = models.FloatField(default=0.0)
    salaire_journalier = models.FloatField(default=0.0)
    salaire_mensuel = models.FloatField(default=0.0)
    salaire_direction = models.FloatField(default=0.0)




