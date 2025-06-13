from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import (
    Budget, CategorieDepense, Depense, Entree, Employe, 
    Notification, PaiementEmploye, MontantSalaire
)


def create_notification(user, message):
    """Fonction utilitaire pour créer une notification"""
    Notification.objects.create(
        user=user,
        message=message,
        created_at=timezone.now()
    )


# Signaux pour Budget
@receiver(post_save, sender=Budget)
def budget_created_updated(sender, instance, created, **kwargs):
    """Signal déclenché lors de la création ou modification d'un budget"""
    if created:
        message = f"✅ Nouveau budget '{instance.nom}' créé avec un montant de {instance.montant} €"
        create_notification(instance.user, message)
    else:
        # Vérifier si le budget est proche de l'épuisement
        if instance.montant <= instance.montant_initial * 0.1:  # 10% restant
            message = f"⚠️ Attention! Votre budget '{instance.nom}' est presque épuisé. Reste: {instance.montant} €"
            create_notification(instance.user, message)
        elif instance.montant <= instance.montant_initial * 0.2:  # 20% restant
            message = f"⚡ Votre budget '{instance.nom}' est faible. Reste: {instance.montant} €"
            create_notification(instance.user, message)


@receiver(post_delete, sender=Budget)
def budget_deleted(sender, instance, **kwargs):
    """Signal déclenché lors de la suppression d'un budget"""
    message = f"🗑️ Budget '{instance.nom}' supprimé"
    create_notification(instance.user, message)


# Signaux pour CategorieDepense
@receiver(post_save, sender=CategorieDepense)
def categorie_depense_created_updated(sender, instance, created, **kwargs):
    """Signal déclenché lors de la création ou modification d'une catégorie de dépense"""
    if created:
        message = f"📂 Nouvelle catégorie '{instance.nom}' créée dans le budget '{instance.id_budget.nom}' avec {instance.montant} €"
        create_notification(instance.user, message)
        
        # Notification pour le budget parent
        budget_message = f"💰 {instance.montant} € alloués à la catégorie '{instance.nom}' du budget '{instance.id_budget.nom}'"
        create_notification(instance.user, budget_message)


@receiver(post_delete, sender=CategorieDepense)
def categorie_depense_deleted(sender, instance, **kwargs):
    """Signal déclenché lors de la suppression d'une catégorie de dépense"""
    message = f"🗑️ Catégorie '{instance.nom}' supprimée du budget '{instance.id_budget.nom}'"
    create_notification(instance.user, message)


# Signaux pour Depense
@receiver(post_save, sender=Depense)
def depense_created_updated(sender, instance, created, **kwargs):
    """Signal déclenché lors de la création ou modification d'une dépense"""
    if created:
        if instance.id_cat_depense:
            message = f"💸 Nouvelle dépense '{instance.nom}': {instance.montant} € dans la catégorie '{instance.id_cat_depense.nom}'"
        else:
            message = f"💸 Nouvelle dépense '{instance.nom}': {instance.montant} € dans le budget '{instance.id_budget.nom}'"
        create_notification(instance.user, message)
        
        # Vérifier si la catégorie est proche de l'épuisement
        if instance.id_cat_depense:
            cat = instance.id_cat_depense
            if cat.montant <= cat.montant_initial * 0.1:
                warning_message = f"⚠️ La catégorie '{cat.nom}' est presque épuisée! Reste: {cat.montant} €"
                create_notification(instance.user, warning_message)


@receiver(post_delete, sender=Depense)
def depense_deleted(sender, instance, **kwargs):
    """Signal déclenché lors de la suppression d'une dépense"""
    message = f"🗑️ Dépense '{instance.nom}' supprimée"
    create_notification(instance.user, message)


# Signaux pour Entree
@receiver(post_save, sender=Entree)
def entree_created_updated(sender, instance, created, **kwargs):
    """Signal déclenché lors de la création ou modification d'une entrée"""
    if created:
        message = f"💰 Nouvelle entrée '{instance.nom}': +{instance.montant} € dans le budget '{instance.id_budget.nom}'"
        create_notification(instance.user, message)


@receiver(post_delete, sender=Entree)
def entree_deleted(sender, instance, **kwargs):
    """Signal déclenché lors de la suppression d'une entrée"""
    message = f"🗑️ Entrée '{instance.nom}' supprimée"
    create_notification(instance.user, message)


# Signaux pour Employe (comptes entreprise seulement)
@receiver(post_save, sender=Employe)
def employe_created_updated(sender, instance, created, **kwargs):
    """Signal déclenché lors de la création ou modification d'un employé"""
    if created:
        message = f"👤 Nouvel employé ajouté: {instance.prenom} {instance.nom} - {instance.poste}"
        create_notification(instance.user, message)
    else:
        # Vérifier changement de statut
        if instance.actif != 'ES':  # Pas en service
            status_labels = dict(instance.ACT)
            message = f"📋 Statut de {instance.prenom} {instance.nom} changé: {status_labels.get(instance.actif, instance.actif)}"
            create_notification(instance.user, message)


@receiver(post_delete, sender=Employe)
def employe_deleted(sender, instance, **kwargs):
    """Signal déclenché lors de la suppression d'un employé"""
    message = f"🗑️ Employé {instance.prenom} {instance.nom} supprimé"
    create_notification(instance.user, message)


# Signaux pour PaiementEmploye
@receiver(post_save, sender=PaiementEmploye)
def paiement_employe_created(sender, instance, created, **kwargs):
    """Signal déclenché lors de la création d'un paiement employé"""
    if created:
        message = f"💵 Paiement de {instance.montant} € effectué à {instance.id_employe.prenom} {instance.id_employe.nom}"
        create_notification(instance.user, message)
        
        # Notification pour le budget
        budget_message = f"💰 {instance.montant} € déduits du budget '{instance.id_budget.nom}' pour le salaire de {instance.id_employe.prenom} {instance.id_employe.nom}"
        create_notification(instance.user, budget_message)


@receiver(post_delete, sender=PaiementEmploye)
def paiement_employe_deleted(sender, instance, **kwargs):
    """Signal déclenché lors de la suppression d'un paiement employé"""
    message = f"🗑️ Paiement de {instance.montant} € à {instance.id_employe.prenom} {instance.id_employe.nom} annulé"
    create_notification(instance.user, message)


# Signal pour vérifier les dates d'échéance des budgets
@receiver(post_save, sender=Budget)  
def check_budget_expiry(sender, instance, created, **kwargs):
    """Vérifier si un budget approche de sa date d'échéance"""
    if not created and instance.date_fin:
        days_remaining = (instance.date_fin - timezone.now().date()).days
        
        if days_remaining <= 3 and days_remaining > 0:
            message = f"⏰ Votre budget '{instance.nom}' expire dans {days_remaining} jour(s)!"
            create_notification(instance.user, message)
        elif days_remaining <= 0:
            message = f"🚨 Votre budget '{instance.nom}' a expiré!"
            create_notification(instance.user, message)


# Signal personnalisé pour les conseils automatiques
@receiver(post_save, sender=Budget)
def generate_budget_advice(sender, instance, created, **kwargs):
    """Générer des conseils automatiques basés sur l'utilisation du budget"""
    if not created:
        usage_percentage = ((instance.montant_initial - instance.montant) / instance.montant_initial) * 100 if instance.montant_initial > 0 else 0
        
        # Conseil si plus de 80% du budget est utilisé
        if usage_percentage >= 80:
            from .models import Conseil
            conseil_message = f"Votre budget '{instance.nom}' est utilisé à {usage_percentage:.1f}%. Considérez réviser vos dépenses ou augmenter le budget."
            
            # Éviter les doublons de conseils
            existing_conseil = Conseil.objects.filter(
                user=instance.user,
                id_budget=instance,
                message__icontains="utilisé à"
            ).exists()
            
            if not existing_conseil:
                Conseil.objects.create(
                    user=instance.user,
                    id_budget=instance,
                    nom="Conseil automatique - Budget",
                    message=conseil_message
                )
                
                # Notification pour le nouveau conseil
                create_notification(instance.user, f"💡 Nouveau conseil disponible pour votre budget '{instance.nom}'")


# Signal pour configuration des salaires
@receiver(post_save, sender=MontantSalaire)
def salaire_config_updated(sender, instance, created, **kwargs):
    """Signal déclenché lors de la configuration des salaires"""
    if created:
        message = "⚙️ Configuration des montants de salaires créée"
    else:
        message = "⚙️ Configuration des montants de salaires mise à jour"
    
    create_notification(instance.user, message)