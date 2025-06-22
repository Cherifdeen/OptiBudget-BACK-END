from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from budgetManager.models import (
    Budget, CategorieDepense, Depense, Entree, Employe, 
    Notification, PaiementEmploye, MontantSalaire, Conseil
)


def create_notification(user, message, type_notif="INFO"):
    """Fonction utilitaire pour créer une notification avec évitement des doublons"""
    # Éviter les notifications en double dans les 5 dernières minutes
    recent_notification = Notification.objects.filter(
        user=user,
        message=message,
        type_notification=type_notif,
        created_at__gte=timezone.now() - timedelta(minutes=5)
    ).first()
    
    if not recent_notification:
        Notification.objects.create(
            user=user,
            message=message,
            created_at=timezone.now()
        )

# ============================================================================
# SIGNAUX POUR BUDGET
# ============================================================================

def _generate_budget_advice(budget_instance):
    """Génère des conseils personnalisés pour le budget selon le type de compte"""
    try:
        # Calculer le pourcentage utilisé
        total_depenses = budget_instance.categorie_depenses.aggregate(
            total=models.Sum('montant_utilise')
        )['total'] or 0
        
        usage_percentage = (total_depenses / budget_instance.montant) * 100 if budget_instance.montant > 0 else 0
        
        # Conseils selon le type de compte
        if budget_instance.user.compte == 'particulier':
            _generate_particulier_advice(budget_instance, usage_percentage)
        elif budget_instance.user.compte == 'entreprise':
            _generate_entreprise_advice(budget_instance, usage_percentage)
        else:
            _generate_generic_advice(budget_instance, usage_percentage)
        
    except Exception as e:
        # Log l'erreur mais ne pas faire échouer le signal
        print(f"Erreur lors de la génération des conseils budget: {e}")


def _generate_particulier_advice(budget_instance, usage_percentage):
    """Génère des conseils spécifiques pour les comptes particuliers"""
    if usage_percentage >= 90:
        message = f"🚨 ATTENTION! Vous avez utilisé {usage_percentage:.1f}% de votre budget personnel '{budget_instance.nom}'. Il est temps de réduire vos dépenses et de revoir vos priorités de consommation."
        notification_type = "ERROR"
    elif usage_percentage >= 75:
        message = f"⚠️ Votre budget personnel '{budget_instance.nom}' est à {usage_percentage:.1f}% d'utilisation. Surveillez vos dépenses et évitez les achats non essentiels cette semaine."
        notification_type = "WARNING"
    elif usage_percentage >= 50:
        message = f"💡 Votre budget personnel '{budget_instance.nom}' est à {usage_percentage:.1f}% d'utilisation. Vous gérez bien vos finances! Continuez sur cette lancée."
        notification_type = "SUCCESS"
    else:
        # Pas de conseil nécessaire pour les budgets peu utilisés
        return
    
    create_notification(budget_instance.user, message, notification_type)


def _generate_entreprise_advice(budget_instance, usage_percentage):
    """Génère des conseils spécifiques pour les comptes entreprise"""
    if usage_percentage >= 90:
        message = f"🚨 URGENT! Votre budget d'entreprise '{budget_instance.nom}' est à {usage_percentage:.1f}% d'utilisation. Réduisez immédiatement les coûts opérationnels et optimisez vos dépenses."
        notification_type = "ERROR"
    elif usage_percentage >= 75:
        message = f"⚠️ Votre budget d'entreprise '{budget_instance.nom}' est à {usage_percentage:.1f}% d'utilisation. Analysez vos coûts et identifiez les optimisations possibles."
        notification_type = "WARNING"
    elif usage_percentage >= 50:
        message = f"💼 Votre budget d'entreprise '{budget_instance.nom}' est à {usage_percentage:.1f}% d'utilisation. Bonne gestion financière! Continuez à optimiser vos processus."
        notification_type = "SUCCESS"
    else:
        # Pas de conseil nécessaire pour les budgets peu utilisés
        return
    
    create_notification(budget_instance.user, message, notification_type)


def _generate_generic_advice(budget_instance, usage_percentage):
    """Génère des conseils génériques pour les autres types de comptes"""
    if usage_percentage >= 90:
        message = f"🚨 Attention! Vous avez utilisé {usage_percentage:.1f}% de votre budget '{budget_instance.nom}'. Réduisez vos dépenses immédiatement."
        notification_type = "WARNING"
    elif usage_percentage >= 75:
        message = f"⚠️ Vous avez utilisé {usage_percentage:.1f}% de votre budget '{budget_instance.nom}'. Surveillez vos dépenses."
        notification_type = "INFO"
    elif usage_percentage >= 50:
        message = f"💡 Vous avez utilisé {usage_percentage:.1f}% de votre budget '{budget_instance.nom}'. Vous êtes sur la bonne voie!"
        notification_type = "SUCCESS"
    else:
        # Pas de conseil nécessaire pour les budgets peu utilisés
        return
    
    create_notification(budget_instance.user, message, notification_type)


@receiver(post_save, sender=Budget)
def budget_post_save_handler(sender, instance, created, **kwargs):
    """Gestionnaire unifié pour les événements post_save du Budget"""
    if created:
        # Notification de création
        message = f"✅ Budget '{instance.nom}' créé avec {instance.montant:,.2f} €"
        create_notification(instance.user, message, "SUCCESS")
    else:
        # Gestion des mises à jour de budget
        _handle_budget_update(instance)
        # Vérifications pour budget existant
        _check_budget_low_funds(instance)
        _check_budget_expiry(instance)
        _generate_budget_advice(instance)


def _handle_budget_update(instance):
    """Gérer les mises à jour de budget"""
    try:
        # Utiliser un flag personnalisé pour tracker les changements
        if hasattr(instance, '_updating_from_serializer'):
            # Cette mise à jour vient du serializer (reset complet)
            message = f"🔄 Budget '{instance.nom}' réinitialisé: {instance.montant:,.2f} €"
            create_notification(instance.user, message, "LOG")
            return
            
        # Pour les autres mises à jour, on peut comparer avec la DB
        old_instance = Budget.objects.get(pk=instance.pk)
        
        # Vérifier changement de nom
        if old_instance.nom != instance.nom:
            message = f"✏️ Budget renommé: '{old_instance.nom}' → '{instance.nom}'"
            create_notification(instance.user, message, "INFO")
        
        # Vérifier changement de montant initial
        if old_instance.montant_initial != instance.montant_initial:
            difference = instance.montant_initial - old_instance.montant_initial
            if difference > 0:
                message = f"📈 Budget '{instance.nom}' augmenté: +{difference:,.2f} €"
                create_notification(instance.user, message, "SUCCESS")
            else:
                message = f"📉 Budget '{instance.nom}' réduit: {difference:,.2f} €"
                create_notification(instance.user, message, "WARNING")
        
        # Vérifier changement de date d'échéance
        if old_instance.date_fin != instance.date_fin:
            if instance.date_fin:
                message = f"📅 Date d'échéance du budget '{instance.nom}' mise à jour: {instance.date_fin}"
            else:
                message = f"📅 Date d'échéance du budget '{instance.nom}' supprimée"
            create_notification(instance.user, message, "LOG")
            
    except Budget.DoesNotExist:
        # Cas où l'instance n'existe pas encore en DB
        pass


def _check_budget_low_funds(instance):
    """Vérifier si le budget a des fonds faibles"""
    if instance.montant_initial > 0:
        remaining_percentage = (instance.montant / instance.montant_initial) * 100
        
        if remaining_percentage <= 5:  # 5% restant
            message = f"🚨 URGENT! Budget '{instance.nom}' critique: {instance.montant:,.2f} € ({remaining_percentage:.1f}%)"
            create_notification(instance.user, message, "ERROR")
        elif remaining_percentage <= 10:  # 10% restant
            message = f"⚠️ Budget '{instance.nom}' très faible: {instance.montant:,.2f} € ({remaining_percentage:.1f}%)"
            create_notification(instance.user, message, "WARNING")
        elif remaining_percentage <= 20:  # 20% restant
            message = f"⚡ Budget '{instance.nom}' faible: {instance.montant:,.2f} € ({remaining_percentage:.1f}%)"
            create_notification(instance.user, message, "WARNING")


def _check_budget_expiry(instance):
    """Vérifier la date d'expiration du budget"""
    if not instance.date_fin:
        return
        
    days_remaining = (instance.date_fin - timezone.now().date()).days
    
    if days_remaining == 0:
        message = f"🚨 Budget '{instance.nom}' expire AUJOURD'HUI!"
        create_notification(instance.user, message, "LOG")
    elif days_remaining == 1:
        message = f"⏰ Budget '{instance.nom}' expire DEMAIN!"
        create_notification(instance.user, message, "LOG")
    elif 2 <= days_remaining <= 7:
        message = f"⏰ Budget '{instance.nom}' expire dans {days_remaining} jours"
        create_notification(instance.user, message, "LOG")
    elif days_remaining < 0:
        message = f"🚨 Budget '{instance.nom}' a expiré il y a {abs(days_remaining)} jour(s)!"
        create_notification(instance.user, message, "LOG")





@receiver(post_delete, sender=Budget)
def budget_deleted_handler(sender, instance, **kwargs):
    """Gestionnaire pour la suppression d'un budget"""
    message = f"🗑️ Budget '{instance.nom}' supprimé"
    create_notification(instance.user, message, "INFO")


# ============================================================================
# SIGNAUX POUR CATEGORIE DEPENSE
# ============================================================================

@receiver(post_save, sender=CategorieDepense)
def categorie_depense_post_save_handler(sender, instance, created, **kwargs):
    """Gestionnaire pour les catégories de dépense"""
    if created:
        message = f"📂 Catégorie '{instance.nom}' créée: {instance.montant:,.2f} € (Budget: {instance.id_budget.nom})"
        create_notification(instance.user, message, "LOG")
    else:
        # Gestion des mises à jour de catégorie
        _handle_category_update(instance)
        # Vérifier les fonds faibles de la catégorie
        _check_category_low_funds(instance)


def _handle_category_update(instance):
    """Gérer les mises à jour de catégorie"""
    try:
        # Récupérer l'ancienne version depuis la DB
        old_instance = CategorieDepense.objects.get(pk=instance.pk)
        
        # Vérifier si le montant a changé
        if old_instance.montant_initial != instance.montant_initial:
            difference = instance.montant_initial - old_instance.montant_initial
            if difference > 0:
                message = f"📈 Catégorie '{instance.nom}' augmentée: +{difference:,.2f} €"
                create_notification(instance.user, message, "LOG")
            else:
                message = f"📉 Catégorie '{instance.nom}' réduite: {difference:,.2f} €"
                create_notification(instance.user, message, "LOG")
        
        # Vérifier si le nom a changé
        if old_instance.nom != instance.nom:
            message = f"✏️ Catégorie renommée: '{old_instance.nom}' → '{instance.nom}'"
            create_notification(instance.user, message, "INFO")
            
    except CategorieDepense.DoesNotExist:
        # Cas où l'instance n'existe pas encore en DB (création)
        pass


def _check_category_low_funds(instance):
    """Vérifier si la catégorie a des fonds faibles"""
    if instance.montant_initial > 0:
        remaining_percentage = (instance.montant / instance.montant_initial) * 100
        
        if remaining_percentage <= 5:
            message = f"🚨 Catégorie '{instance.nom}' critique: {instance.montant:,.2f} €"
            create_notification(instance.user, message, "LOG")
        elif remaining_percentage <= 15:
            message = f"⚠️ Catégorie '{instance.nom}' faible: {instance.montant:,.2f} €"
            create_notification(instance.user, message, "LOG")


@receiver(post_delete, sender=CategorieDepense)
def categorie_depense_deleted_handler(sender, instance, **kwargs):
    """Gestionnaire pour suppression de catégorie"""
    message = f"🗑️ Catégorie '{instance.nom}' supprimée"
    create_notification(instance.user, message, "INFO")


# ============================================================================
# SIGNAUX POUR DEPENSE
# ============================================================================

@receiver(post_save, sender=Depense)
def depense_post_save_handler(sender, instance, created, **kwargs):
    """Gestionnaire pour les dépenses"""
    if created:
        if instance.id_cat_depense:
            message = f"💸 Dépense '{instance.nom}': {instance.montant:,.2f} € (Catégorie: {instance.id_cat_depense.nom})"
        else:
            message = f"💸 Dépense '{instance.nom}': {instance.montant:,.2f} € (Budget: {instance.id_budget.nom})"
        
        create_notification(instance.user, message, "LOG")
        
        # Vérifier l'impact sur la catégorie
        if instance.id_cat_depense:
            _check_category_low_funds(instance.id_cat_depense)
    else:
        # Gestion des mises à jour de dépense
        _handle_depense_update(instance)


def _handle_depense_update(instance):
    """Gérer les mises à jour de dépense"""
    try:
        old_instance = Depense.objects.get(pk=instance.pk)
        
        # Vérifier changement de montant
        if old_instance.montant != instance.montant:
            difference = instance.montant - old_instance.montant
            if difference > 0:
                message = f"📈 Dépense '{instance.nom}' augmentée: +{difference:,.2f} €"
                create_notification(instance.user, message, "LOG")
            else:
                message = f"📉 Dépense '{instance.nom}' réduite: {difference:,.2f} €"
                create_notification(instance.user, message, "LOG")
        
        # Vérifier changement de nom
        if old_instance.nom != instance.nom:
            message = f"✏️ Dépense renommée: '{old_instance.nom}' → '{instance.nom}'"
            create_notification(instance.user, message, "LOG")
        
        # Vérifier changement de catégorie
        if old_instance.id_cat_depense != instance.id_cat_depense:
            old_cat = old_instance.id_cat_depense.nom if old_instance.id_cat_depense else "Aucune"
            new_cat = instance.id_cat_depense.nom if instance.id_cat_depense else "Aucune"
            message = f"📁 Dépense '{instance.nom}' déplacée: {old_cat} → {new_cat}"
            create_notification(instance.user, message, "LOG")
            
    except Depense.DoesNotExist:
        pass


@receiver(pre_delete, sender=Depense)
def depense_pre_delete_handler(sender, instance, **kwargs):
    """Gestionnaire avant suppression de dépense - pour restaurer les montants"""
    # Restaurer les montants avant suppression
    if instance.id_cat_depense:
        instance.id_cat_depense.montant += instance.montant
        instance.id_cat_depense.save()
    
    instance.id_budget.montant += instance.montant
    instance.id_budget.save()


@receiver(post_delete, sender=Depense)
def depense_post_delete_handler(sender, instance, **kwargs):
    """Gestionnaire après suppression de dépense"""
    message = f"🗑️ Dépense '{instance.nom}' annulée: +{instance.montant:,.2f} € restaurés"
    create_notification(instance.user, message, "LOG")


# ============================================================================
# SIGNAUX POUR ENTREE
# ============================================================================

@receiver(post_save, sender=Entree)
def entree_post_save_handler(sender, instance, created, **kwargs):
    """Gestionnaire pour les entrées"""
    if created:
        message = f"💰 Entrée '{instance.nom}': +{instance.montant:,.2f} € (Budget: {instance.id_budget.nom})"
        create_notification(instance.user, message, "LOG")
        
        # Ajouter le montant au budget
        instance.id_budget.montant += instance.montant
        instance.id_budget.save()
    else:
        # Gestion des mises à jour d'entrée
        _handle_entree_update(instance)


def _handle_entree_update(instance):
    """Gérer les mises à jour d'entrée"""
    try:
        old_instance = Entree.objects.get(pk=instance.pk)
        
        # Vérifier changement de montant
        if old_instance.montant != instance.montant:
            difference = instance.montant - old_instance.montant
            
            # Ajuster le budget avec la différence
            instance.id_budget.montant += difference
            instance.id_budget.save()
            
            if difference > 0:
                message = f"📈 Entrée '{instance.nom}' augmentée: +{difference:,.2f} €"
                create_notification(instance.user, message, "LOG")
            else:
                message = f"📉 Entrée '{instance.nom}' réduite: {difference:,.2f} €"
                create_notification(instance.user, message, "LOG")
        
        # Vérifier changement de nom
        if old_instance.nom != instance.nom:
            message = f"✏️ Entrée renommée: '{old_instance.nom}' → '{instance.nom}'"
            create_notification(instance.user, message, "LOG")
            
    except Entree.DoesNotExist:
        pass


@receiver(pre_delete, sender=Entree)
def entree_pre_delete_handler(sender, instance, **kwargs):
    """Gestionnaire avant suppression d'entrée"""
    # Déduire le montant du budget
    instance.id_budget.montant -= instance.montant
    instance.id_budget.save()


@receiver(post_delete, sender=Entree)
def entree_post_delete_handler(sender, instance, **kwargs):
    """Gestionnaire après suppression d'entrée"""
    message = f"🗑️ Entrée '{instance.nom}' supprimée: -{instance.montant:,.2f} €"
    create_notification(instance.user, message, "INFO")


# ============================================================================
# SIGNAUX POUR EMPLOYE (Comptes Entreprise)
# ============================================================================
@receiver(post_save, sender=Employe)
def employe_post_save_handler(sender, instance, created, **kwargs):
    """Gestionnaire pour les employés"""
    if created:
        message = f"👤 Employé ajouté: {instance.prenom} {instance.nom} - {instance.poste}"
        create_notification(instance.user, message, "LOG")
    else:
        # Notification pour changement de statut
        if hasattr(instance, '_state') and instance._state.adding is False:
            check_employee_status_change(instance)

def check_employee_status_change(instance):
    """Vérifier les changements de statut d'employé"""
    try:
        old_instance = Employe.objects.get(pk=instance.pk)
        
        # Vérifier changement de statut
        if old_instance.actif != instance.actif:
            status_labels = dict(Employe.ACT)
            old_status = status_labels.get(old_instance.actif, old_instance.actif)
            new_status = status_labels.get(instance.actif, instance.actif)
            message = f"📋 {instance.prenom} {instance.nom}: {old_status} → {new_status}"
            # Type de notification selon le nouveau statut
            notif_type = "WARNING" if instance.actif in ['LC', 'HS', 'DM'] else "INFO"  # Fixed status codes
            create_notification(instance.user, message, notif_type)
        
        # Vérifier autres changements importants
        changes = []
        if old_instance.poste != instance.poste:
            changes.append(f"poste: {old_instance.poste} → {instance.poste}")
        # Removed salary comparison since Employe model doesn't have salaire field
        if old_instance.email != instance.email:
            changes.append(f"email: {old_instance.email} → {instance.email}")
        if old_instance.telephone != instance.telephone:
            changes.append(f"téléphone: {old_instance.telephone} → {instance.telephone}")
        if old_instance.type_employe != instance.type_employe:
            type_labels = dict(Employe.TYPE_EMPLOYE_CHOICES)
            old_type = type_labels.get(old_instance.type_employe, old_instance.type_employe)
            new_type = type_labels.get(instance.type_employe, instance.type_employe)
            changes.append(f"type: {old_type} → {new_type}")
            
        if changes:
            message = f"✏️ {instance.prenom} {instance.nom} - Mis à jour: {', '.join(changes)}"
            create_notification(instance.user, message, "LOG")
            
    except Employe.DoesNotExist:
        pass

@receiver(post_delete, sender=Employe)
def employe_deleted_handler(sender, instance, **kwargs):
    """Gestionnaire pour suppression d'employé"""
    message = f"🗑️ Employé supprimé: {instance.prenom} {instance.nom}"
    create_notification(instance.user, message, "INFO")

# ============================================================================
# SIGNAUX POUR PAIEMENT EMPLOYE
# ============================================================================

@receiver(post_save, sender=PaiementEmploye)
def paiement_employe_post_save_handler(sender, instance, created, **kwargs):
    """Gestionnaire pour les paiements d'employés"""
    if created:
        employe_nom = f"{instance.id_employe.prenom} {instance.id_employe.nom}"
        message = f"💵 Salaire payé: {instance.montant:,.2f} € à {employe_nom}"
        create_notification(instance.user, message, "LOG")
        
        # Notification budget si fonds faibles après paiement
        if instance.id_budget.montant <= instance.id_budget.montant_initial * 0.2:
            budget_message = f"⚠️ Budget '{instance.id_budget.nom}' faible après paiement salaire"
            create_notification(instance.user, budget_message, "WARNING")


@receiver(post_delete, sender=PaiementEmploye)
def paiement_employe_deleted_handler(sender, instance, **kwargs):
    """Gestionnaire pour suppression de paiement"""
    employe_nom = f"{instance.id_employe.prenom} {instance.id_employe.nom}"
    message = f"🗑️ Paiement annulé: {instance.montant:,.2f} € pour {employe_nom}"
    create_notification(instance.user, message, "LOG")


# ============================================================================
# SIGNAUX POUR MONTANT SALAIRE
# ============================================================================

@receiver(post_save, sender=MontantSalaire)
def montant_salaire_post_save_handler(sender, instance, created, **kwargs):
    """Gestionnaire pour configuration des salaires"""
    if created:
        message = "⚙️ Configuration des salaires créée"
        create_notification(instance.user, message, "LOG")
    else:
        message = "⚙️ Configuration des salaires mise à jour"
        create_notification(instance.user, message, "LOG")


# ============================================================================
# SIGNAUX PERSONNALISÉS POUR CONSEILS ET ANALYSES
# ============================================================================

@receiver(post_save, sender=Conseil)
def conseil_post_save_handler(sender, instance, created, **kwargs):
    """Gestionnaire pour les conseils"""
    if created and not instance.nom.startswith("Conseil Auto"):
        # Seulement pour les conseils manuels
        message = f"💡 Nouveau conseil ajouté: {instance.nom}"
        create_notification(instance.user, message, "LOG")


# ============================================================================
# MODIFICATION REQUISE DANS LES SERIALIZERS
# ============================================================================

# IMPORTANT: Ajoutez cette méthode dans votre BudgetSerializer.update()
# Pour marquer les mises à jour venant du serializer:

"""
def update(self, instance, validated_data):
    # Marquer que cette mise à jour vient du serializer
    instance._updating_from_serializer = True
    
    # ... votre code existant de mise à jour ...
    
    # Mettre à jour le montant_initial avec le nouveau montant
    nouveau_montant = validated_data.get('montant', instance.montant)
    validated_data['montant_initial'] = nouveau_montant
    
    return super().update(instance, validated_data)
"""

def cleanup_old_notifications(user, days=30):
    """Nettoyer les anciennes notifications (à appeler périodiquement)"""
    cutoff_date = timezone.now() - timedelta(days=days)
    old_notifications = Notification.objects.filter(
        user=user,
        created_at__lt=cutoff_date
    )
    count = old_notifications.count()
    old_notifications.delete()
    return count