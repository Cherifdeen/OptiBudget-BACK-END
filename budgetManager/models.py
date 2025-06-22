from django.db import models
from django.conf import settings  
import uuid
from django.core.exceptions import ValidationError
from django.utils import timezone

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
    actif = models.BooleanField(default=True)
    D = [
        ('D', 'Durée determiner'),
        ('I', 'Durée non determiner'),
    ]
    type_budget = models.CharField(max_length=3, choices=D, default='D')
    bilan_fait = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.nom} - {self.user.email}"
    
    def get_montant_utilise(self):
        """Calculer le montant utilisé du budget"""
        return self.montant_initial - self.montant
    
    def get_pourcentage_utilise(self):
        """Calculer le pourcentage utilisé du budget"""
        if self.montant_initial > 0:
            return round((self.get_montant_utilise() / self.montant_initial) * 100, 2)
        return 0.0
    
    def get_pourcentage_restant(self):
        """Calculer le pourcentage restant du budget"""
        return 100 - self.get_pourcentage_utilise()
    
    def get_jours_restants(self):
        """Calculer le nombre de jours restants avant expiration"""
        if not self.date_fin:
            return None
        return (self.date_fin - timezone.now().date()).days
    
    def is_expired(self):
        """Vérifier si le budget est expiré"""
        if not self.date_fin:
            return False
        return self.date_fin < timezone.now().date()
    
    def is_critical(self, seuil=10):
        """Vérifier si le budget est critique (moins de X% restant)"""
        return self.get_pourcentage_restant() <= seuil
    
    def get_total_depenses(self):
        """Calculer le total des dépenses du budget"""
        from django.db.models import Sum
        return Depense.objects.filter(id_budget=self).aggregate(
            total=Sum('montant')
        )['total'] or 0.0
    
    def get_total_entrees(self):
        """Calculer le total des entrées du budget (entreprise uniquement)"""
        from django.db.models import Sum
        if self.user.compte == 'entreprise':
            return Entree.objects.filter(id_budget=self).aggregate(
                total=Sum('montant')
            )['total'] or 0.0
        return 0.0
    
    def get_total_paiements_employes(self):
        """Calculer le total des paiements d'employés (entreprise uniquement)"""
        from django.db.models import Sum
        if self.user.compte == 'entreprise':
            return PaiementEmploye.objects.filter(id_budget=self).aggregate(
                total=Sum('montant')
            )['total'] or 0.0
        return 0.0
    
    def get_solde_actuel(self):
        """Calculer le solde actuel du budget"""
        return self.montant + self.get_total_entrees() - self.get_total_paiements_employes()
    
    def get_statistiques_categories(self):
        """Obtenir les statistiques par catégorie"""
        categories = CategorieDepense.objects.filter(id_budget=self)
        stats = []
        
        for categorie in categories:
            depenses_cat = Depense.objects.filter(id_cat_depense=categorie)
            total_depenses = depenses_cat.aggregate(
                total=models.Sum('montant')
            )['total'] or 0.0
            
            stats.append({
                'categorie': categorie.nom,
                'montant_initial': categorie.montant_initial,
                'montant_restant': categorie.montant,
                'montant_utilise': total_depenses,
                'pourcentage_utilise': round((total_depenses / categorie.montant_initial) * 100, 2) if categorie.montant_initial > 0 else 0,
                'nombre_depenses': depenses_cat.count()
            })
        
        return stats
    
    def can_add_categorie(self, montant):
        """Vérifier si on peut ajouter une catégorie avec ce montant"""
        return self.montant >= montant
    
    def add_categorie(self, nom, montant, description=""):
        """Ajouter une catégorie au budget"""
        if not self.can_add_categorie(montant):
            raise ValidationError(f"Montant insuffisant dans le budget. Disponible: {self.montant}")
        
        categorie = CategorieDepense.objects.create(
            nom=nom,
            montant=montant,
            montant_initial=montant,
            description=description,
            id_budget=self,
            user=self.user
        )
        
        # Mettre à jour le montant du budget
        self.montant -= montant
        self.save()
        
        return categorie
    
    def reset_budget(self):
        """Réinitialiser le budget à son montant initial"""
        self.montant = self.montant_initial
        self.save()
        
        # Supprimer toutes les catégories et dépenses
        CategorieDepense.objects.filter(id_budget=self).delete()
        Depense.objects.filter(id_budget=self).delete()
        Entree.objects.filter(id_budget=self).delete()
        PaiementEmploye.objects.filter(id_budget=self).delete()


class CategorieDepense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100,unique=True)
    description = models.TextField(null=True, blank=True)
    montant = models.FloatField(default=0.0)
    montant_initial = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id_budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  


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
    id_cat_depense = models.ForeignKey(CategorieDepense, null=True, blank=True, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  


class Entree(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100)
    montant = models.FloatField(default=0.0)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id_budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  


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
        ('AUT', 'Autre'),  
    ]
    type_employe = models.CharField(max_length=3, choices=TYPE_EMPLOYE_CHOICES, default='AUT')
    poste = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
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
        ('ER', 'Retraité'),  
        ('LC', 'Licencié'),
        ('HS', 'Hors service'),
        ('DM', 'Démissionné'),  
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE)  
    viewed = models.BooleanField(default=False)


class Conseil(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_budget = models.ForeignKey(Budget, on_delete=models.CASCADE, null=True, blank=True)
    nom = models.TextField(default='conseil')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
    viewed = models.BooleanField(default=False)


class PaiementEmploye(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_employe = models.ForeignKey(Employe, on_delete=models.CASCADE)
    montant = models.FloatField(default=0.0)
    date_paiement = models.DateTimeField(auto_now_add=True)
    type_paiement = models.CharField(max_length=50, choices=[('SALAIRE', 'Salaire')])
    description = models.TextField(blank=True, null=True)
    id_budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class MontantSalaire(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
    
    # Salaires par type d'employé
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

    # Salaires par période
    salaire_hebdomadaire = models.FloatField(default=0.0)
    salaire_horaire = models.FloatField(default=0.0)
    salaire_journalier = models.FloatField(default=0.0)
    salaire_mensuel = models.FloatField(default=0.0)
    
    # Métadonnées
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuration des salaires"
        verbose_name_plural = "Configurations des salaires"
    
    def __str__(self):
        return f"Configuration salaires - {self.user.email}"
    
    def get_salaire_by_type(self, type_employe):
        """Récupérer le salaire selon le type d'employé"""
        mapping = {
            'DIR': self.salaire_direction,
            'CAD': self.salaire_cadre,
            'EMP': self.salaire_employe,
            'OUV': self.salaire_ouvrier,
            'CON': self.salaire_cf,
            'STA': self.salaire_stagiaire,
            'INT': self.salaire_intermediaire,
            'AUT': self.salaire_autre,
        }
        return mapping.get(type_employe, 0.0)
    
    def get_bonus_by_type(self, type_employe):
        """Récupérer le bonus selon le type d'employé"""
        mapping = {
            'DIR': self.bonus_direction,
            'CAD': self.bonus_cadre,
            'EMP': self.bonus_employe,
            'OUV': self.bonus_ouvrier,
            'CON': self.bonus_cf,
            'STA': self.bonus_stagiaire,
            'INT': self.bonus_intermediaire,
            'AUT': self.bonus_autre,
        }
        return mapping.get(type_employe, 0.0)
    
    def get_indemnite_by_type(self, type_employe):
        """Récupérer l'indemnité selon le type d'employé"""
        mapping = {
            'DIR': self.indemnite_direction,
            'CAD': self.indemnite_cadre,
            'EMP': self.indemnite_employe,
            'OUV': self.indemnite_ouvrier,
            'CON': self.indemnite_cf,
            'STA': self.indemnite_stagiaire,
            'INT': self.indemnite_intermediaire,
            'AUT': self.indemnite_autre,
        }
        return mapping.get(type_employe, 0.0)
    
    def get_avance_by_type(self, type_employe):
        """Récupérer l'avance selon le type d'employé"""
        mapping = {
            'DIR': self.avance_direction,
            'CAD': self.avance_cadre,
            'EMP': self.avance_employe,
            'OUV': self.avance_ouvrier,
            'CON': self.avance_cf,
            'STA': self.avance_stagiaire,
            'INT': self.avance_intermediaire,
            'AUT': self.avance_autre,
        }
        return mapping.get(type_employe, 0.0)
    
    def get_total_by_type(self, type_employe):
        """Calculer le total (salaire + bonus + indemnité - avance) selon le type d'employé"""
        salaire = self.get_salaire_by_type(type_employe)
        bonus = self.get_bonus_by_type(type_employe)
        indemnite = self.get_indemnite_by_type(type_employe)
        avance = self.get_avance_by_type(type_employe)
        
        return salaire + bonus + indemnite - avance
    
    def get_total_mensuel(self):
        """Calculer le total mensuel de tous les salaires"""
        return sum([
            self.get_total_by_type('DIR'),
            self.get_total_by_type('CAD'),
            self.get_total_by_type('EMP'),
            self.get_total_by_type('OUV'),
            self.get_total_by_type('CON'),
            self.get_total_by_type('STA'),
            self.get_total_by_type('INT'),
            self.get_total_by_type('AUT'),
        ])
    
    def update_from_period(self, period_type, amount):
        """Mettre à jour les salaires basés sur une période de référence"""
        if period_type == 'mensuel':
            self.salaire_mensuel = amount
            self.salaire_hebdomadaire = amount / 4.33
            self.salaire_journalier = amount / 30
            self.salaire_horaire = amount / (30 * 8)
        elif period_type == 'hebdomadaire':
            self.salaire_hebdomadaire = amount
            self.salaire_mensuel = amount * 4.33
            self.salaire_journalier = amount / 7
            self.salaire_horaire = amount / (7 * 8)
        elif period_type == 'journalier':
            self.salaire_journalier = amount
            self.salaire_mensuel = amount * 30
            self.salaire_hebdomadaire = amount * 7
            self.salaire_horaire = amount / 8
        elif period_type == 'horaire':
            self.salaire_horaire = amount
            self.salaire_journalier = amount * 8
            self.salaire_hebdomadaire = amount * 8 * 7
            self.salaire_mensuel = amount * 8 * 30




