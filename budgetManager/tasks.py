# tasks.py
from celery import shared_task
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db import transaction
from datetime import datetime, timedelta
import google.generativeai as genai
from django.conf import settings
import json
import logging
from .models import Budget, CategorieDepense, Depense, Entree, Conseil, Notification

logger = logging.getLogger(__name__)

# Configuration de Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

@shared_task
def marquer_budgets_expires():
    """
    Marque les budgets expirés (date_fin dépassée) comme inactifs
    """
    try:
        aujourd_hui = timezone.now().date()
        budgets_expires = Budget.objects.filter(
            date_fin__lt=aujourd_hui,
            actif=True,
            type_budget='D'  # Durée déterminée
        )
        
        count = budgets_expires.count()
        budgets_expires.update(actif=False)
        
        logger.info(f"{count} budgets marqués comme expirés")
        return f"{count} budgets marqués comme expirés"
        
    except Exception as e:
        logger.error(f"Erreur lors du marquage des budgets expirés: {str(e)}")
        return f"Erreur: {str(e)}"


@shared_task
def generer_statistiques_hebdomadaires():
    """
    Génère les statistiques hebdomadaires pour tous les budgets actifs
    à durée indéterminée
    """
    try:
        # Budgets à durée indéterminée et actifs
        budgets = Budget.objects.filter(
            type_budget='I',  # Durée indéterminée
            actif=True
        ).select_related('user')
        
        resultats = []
        
        for budget in budgets:
            try:
                stats = generer_statistiques_budget(budget, 'hebdomadaire')
                conseil = generer_conseil_ia(budget, stats, 'hebdomadaire')
                
                # Sauvegarder le conseil
                Conseil.objects.create(
                    id_budget=budget,
                    nom=f"Conseil hebdomadaire - {timezone.now().strftime('%Y-%m-%d')}",
                    message=conseil,
                    user=budget.user
                )
                
                # Créer une notification
                Notification.objects.create(
                    message=f"Nouveau conseil hebdomadaire disponible pour le budget '{budget.nom}'",
                    type_notification='INFO',
                    user=budget.user
                )
                
                resultats.append(f"Statistiques générées pour budget {budget.nom}")
                
            except Exception as e:
                logger.error(f"Erreur pour budget {budget.nom}: {str(e)}")
                resultats.append(f"Erreur pour budget {budget.nom}: {str(e)}")
        
        return f"Statistiques hebdomadaires générées: {len(resultats)} budgets traités"
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des statistiques hebdomadaires: {str(e)}")
        return f"Erreur: {str(e)}"


@shared_task
def generer_statistiques_budgets_expires():
    """
    Génère les statistiques finales pour les budgets expirés
    et marque bilan_fait à True
    """
    try:
        budgets_expires = Budget.objects.filter(
            actif=False,
            bilan_fait=False,
            type_budget='D'  # Durée déterminée
        ).select_related('user')
        
        resultats = []
        
        for budget in budgets_expires:
            try:
                with transaction.atomic():
                    stats = generer_statistiques_budget(budget, 'final')
                    conseil = generer_conseil_ia(budget, stats, 'final')
                    
                    # Sauvegarder le conseil final
                    Conseil.objects.create(
                        id_budget=budget,
                        nom=f"Bilan final - {budget.nom}",
                        message=conseil,
                        user=budget.user
                    )
                    
                    # Marquer le bilan comme fait
                    budget.bilan_fait = True
                    budget.save()
                    
                    # Créer une notification
                    Notification.objects.create(
                        message=f"Bilan final disponible pour le budget '{budget.nom}'",
                        type_notification='SUCCESS',
                        user=budget.user
                    )
                    
                    resultats.append(f"Bilan final généré pour budget {budget.nom}")
                    
            except Exception as e:
                logger.error(f"Erreur pour budget {budget.nom}: {str(e)}")
                resultats.append(f"Erreur pour budget {budget.nom}: {str(e)}")
        
        return f"Bilans finaux générés: {len(resultats)} budgets traités"
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des bilans finaux: {str(e)}")
        return f"Erreur: {str(e)}"


def generer_statistiques_budget(budget, type_periode):
    """
    Génère les statistiques détaillées d'un budget
    """
    try:
        # Calculer la période
        if type_periode == 'hebdomadaire':
            date_debut = timezone.now() - timedelta(days=7)
        else:  # final
            date_debut = budget.created_at
        
        date_fin = timezone.now()
        
        # Statistiques générales
        total_depenses = Depense.objects.filter(
            id_budget=budget,
            created_at__gte=date_debut,
            created_at__lte=date_fin
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Statistiques par catégorie
        stats_categories = []
        categories = CategorieDepense.objects.filter(id_budget=budget)
        
        for categorie in categories:
            depenses_cat = Depense.objects.filter(
                id_cat_depense=categorie,
                created_at__gte=date_debut,
                created_at__lte=date_fin
            ).aggregate(
                total=Sum('montant'),
                count=Count('id')
            )
            
            pourcentage = 0
            if categorie.montant_initial > 0:
                pourcentage = (depenses_cat['total'] or 0) / categorie.montant_initial * 100
            
            stats_categories.append({
                'nom': categorie.nom,
                'montant_initial': categorie.montant_initial,
                'montant_depense': depenses_cat['total'] or 0,
                'nombre_depenses': depenses_cat['count'] or 0,
                'pourcentage_utilise': round(pourcentage, 2),
                'montant_restant': categorie.montant_initial - (depenses_cat['total'] or 0)
            })
        
        # Statistiques des entrées (pour les comptes entreprise)
        total_entrees = 0
        if budget.user.compte == 'entreprise':
            total_entrees = Entree.objects.filter(
                id_budget=budget,
                created_at__gte=date_debut,
                created_at__lte=date_fin
            ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Statistiques par type de dépense
        stats_types = Depense.objects.filter(
            id_budget=budget,
            created_at__gte=date_debut,
            created_at__lte=date_fin
        ).values('type_depense').annotate(
            total=Sum('montant'),
            count=Count('id')
        )
        
        # Calculs de ratios
        solde_actuel = budget.montant_initial + total_entrees - total_depenses
        taux_utilisation = 0
        if budget.montant_initial > 0:
            taux_utilisation = (total_depenses / budget.montant_initial) * 100
        
        return {
            'budget_nom': budget.nom,
            'periode': type_periode,
            'date_debut': date_debut.strftime('%Y-%m-%d'),
            'date_fin': date_fin.strftime('%Y-%m-%d'),
            'montant_initial': budget.montant_initial,
            'total_depenses': total_depenses,
            'total_entrees': total_entrees,
            'solde_actuel': solde_actuel,
            'taux_utilisation': round(taux_utilisation, 2),
            'categories': stats_categories,
            'types_depenses': list(stats_types),
            'nombre_total_depenses': Depense.objects.filter(
                id_budget=budget,
                created_at__gte=date_debut,
                created_at__lte=date_fin
            ).count(),
            'compte_type': budget.user.compte,
            'devise': budget.user.devise
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des statistiques: {str(e)}")
        raise


def generer_conseil_ia(budget, stats, type_periode):
    """
    Génère un conseil personnalisé avec l'API Gemini selon le type de compte
    """
    try:
        compte_type = stats['compte_type']
        
        if compte_type == 'particulier':
            return _generer_conseil_particulier(budget, stats, type_periode)
        elif compte_type == 'entreprise':
            return _generer_conseil_entreprise(budget, stats, type_periode)
        else:
            return _generer_conseil_generique(budget, stats, type_periode)
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du conseil IA: {str(e)}")
        return f"Erreur lors de la génération du conseil automatique. Veuillez consulter vos statistiques manuellement."


def _generer_conseil_particulier(budget, stats, type_periode):
    """
    Génère des conseils spécifiques pour les comptes particuliers
    """
    if type_periode == 'hebdomadaire':
        prompt = f"""
        En tant qu'expert en gestion financière personnelle, analysez les statistiques hebdomadaires suivantes et fournissez des conseils adaptés à un particulier :

        **BUDGET PERSONNEL: {stats['budget_nom']}**
        - Devise: {stats['devise']}
        - Montant initial: {stats['montant_initial']}
        - Dépenses cette semaine: {stats['total_depenses']}
        - Solde actuel: {stats['solde_actuel']}
        - Taux d'utilisation: {stats['taux_utilisation']}%

        **DÉPENSES PAR CATÉGORIE:**
        """
        
        for cat in stats['categories']:
            prompt += f"\n- {cat['nom']}: {cat['montant_depense']}/{cat['montant_initial']} ({cat['pourcentage_utilise']}%)"
        
        prompt += f"""

        **CONSEILS DEMANDÉS (Format structuré):**

        📊 **ANALYSE DE LA SEMAINE**
        - Évaluez votre gestion budgétaire cette semaine
        - Identifiez vos points forts et vos difficultés

        💡 **CONSEILS PRATIQUES**
        - 3-4 actions concrètes pour améliorer votre gestion
        - Astuces pour réduire les dépenses non essentielles
        - Conseils pour optimiser vos achats quotidiens

        ⚠️ **ALERTES ET RISQUES**
        - Catégories qui nécessitent votre attention
        - Risques de dépassement de budget
        - Conseils pour éviter les achats impulsifs

        🎯 **OBJECTIFS POUR LA SEMAINE PROCHAINE**
        - Objectifs réalistes à atteindre
        - Stratégies pour mieux gérer vos dépenses
        - Conseils pour maintenir un bon équilibre

        Réponse en français, format structuré avec des emojis et des sections claires.
        """
    
    else:  # final
        prompt = f"""
        En tant qu'expert en gestion financière personnelle, analysez le bilan final de ce budget personnel et fournissez des recommandations :

        **BILAN FINAL - BUDGET PERSONNEL: {stats['budget_nom']}**
        - Période: du {stats['date_debut']} au {stats['date_fin']}
        - Montant initial: {stats['montant_initial']}
        - Total dépenses: {stats['total_depenses']}
        - Solde final: {stats['solde_actuel']}
        - Taux d'utilisation: {stats['taux_utilisation']}%

        **PERFORMANCE PAR CATÉGORIE:**
        """
        
        for cat in stats['categories']:
            prompt += f"\n- {cat['nom']}: {cat['montant_depense']}/{cat['montant_initial']} ({cat['pourcentage_utilise']}%)"
        
        prompt += f"""

        **ANALYSE DEMANDÉE (Format structuré):**

        🏆 **BILAN GLOBAL**
        - Évaluation de votre gestion budgétaire
        - Points forts de votre approche
        - Domaines d'amélioration identifiés

        📈 **LEÇONS APPRISES**
        - Ce que vous avez bien géré
        - Les erreurs à éviter à l'avenir
        - Comportements à maintenir

        💰 **RECOMMANDATIONS POUR L'AVENIR**
        - Stratégies pour vos futurs budgets
        - Conseils pour optimiser vos dépenses
        - Objectifs financiers à fixer

        🎯 **PLAN D'ACTION**
        - Actions concrètes pour améliorer
        - Habitudes à développer
        - Conseils pour maintenir l'équilibre

        Réponse en français, format structuré avec des emojis et des sections claires.
        """
    
    # Appel à l'API Gemini
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    
    return response.text


def _generer_conseil_entreprise(budget, stats, type_periode):
    """
    Génère des conseils spécifiques pour les comptes entreprise
    """
    if type_periode == 'hebdomadaire':
        prompt = f"""
        En tant qu'expert en gestion financière d'entreprise, analysez les statistiques hebdomadaires suivantes et fournissez des conseils adaptés à une entreprise :

        **BUDGET ENTREPRISE: {stats['budget_nom']}**
        - Devise: {stats['devise']}
        - Montant initial: {stats['montant_initial']}
        - Dépenses cette semaine: {stats['total_depenses']}
        - Entrées/Revenus cette semaine: {stats['total_entrees']}
        - Solde actuel: {stats['solde_actuel']}
        - Taux d'utilisation: {stats['taux_utilisation']}%

        **DÉPENSES PAR CATÉGORIE:**
        """
        
        for cat in stats['categories']:
            prompt += f"\n- {cat['nom']}: {cat['montant_depense']}/{cat['montant_initial']} ({cat['pourcentage_utilise']}%)"
        
        prompt += f"""

        **CONSEILS DEMANDÉS (Format structuré):**

        📊 **ANALYSE FINANCIÈRE DE LA SEMAINE**
        - Évaluation de la santé financière de l'entreprise
        - Analyse des flux de trésorerie
        - Performance par rapport aux objectifs

        💼 **GESTION OPÉRATIONNELLE**
        - Optimisation des coûts opérationnels
        - Conseils pour améliorer la rentabilité
        - Stratégies de réduction des dépenses

        📈 **STRATÉGIE FINANCIÈRE**
        - Recommandations pour maximiser les revenus
        - Conseils pour équilibrer dépenses et investissements
        - Stratégies de croissance financière

        ⚠️ **GESTION DES RISQUES**
        - Alertes sur les catégories critiques
        - Conseils pour éviter les dépassements
        - Stratégies de prévention des difficultés

        🎯 **OBJECTIFS POUR LA SEMAINE PROCHAINE**
        - Objectifs financiers réalistes
        - Actions prioritaires à entreprendre
        - Conseils pour maintenir la performance

        Réponse en français, format structuré avec des emojis et des sections claires.
        """
    
    else:  # final
        prompt = f"""
        En tant qu'expert en gestion financière d'entreprise, analysez le bilan final de ce budget d'entreprise et fournissez des recommandations stratégiques :

        **BILAN FINAL - BUDGET ENTREPRISE: {stats['budget_nom']}**
        - Période: du {stats['date_debut']} au {stats['date_fin']}
        - Montant initial: {stats['montant_initial']}
        - Total dépenses: {stats['total_depenses']}
        - Total entrées/revenus: {stats['total_entrees']}
        - Solde final: {stats['solde_actuel']}
        - Taux d'utilisation: {stats['taux_utilisation']}%

        **PERFORMANCE PAR CATÉGORIE:**
        """
        
        for cat in stats['categories']:
            prompt += f"\n- {cat['nom']}: {cat['montant_depense']}/{cat['montant_initial']} ({cat['pourcentage_utilise']}%)"
        
        prompt += f"""

        **ANALYSE DEMANDÉE (Format structuré):**

        🏢 **BILAN STRATÉGIQUE**
        - Évaluation globale de la gestion financière
        - Performance par rapport aux objectifs business
        - Impact sur la rentabilité de l'entreprise

        📊 **ANALYSE DES PERFORMANCES**
        - Catégories les plus performantes
        - Domaines nécessitant des améliorations
        - Efficacité de l'allocation des ressources

        💡 **RECOMMANDATIONS STRATÉGIQUES**
        - Optimisations pour les futurs budgets
        - Stratégies d'amélioration de la rentabilité
        - Conseils pour la croissance financière

        🎯 **PLAN D'ACTION FUTUR**
        - Actions prioritaires à entreprendre
        - Objectifs financiers à fixer
        - Stratégies de développement

        Réponse en français, format structuré avec des emojis et des sections claires.
        """
    
    # Appel à l'API Gemini
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    
    return response.text


def _generer_conseil_generique(budget, stats, type_periode):
    """
    Génère des conseils génériques pour les autres types de comptes
    """
    if type_periode == 'hebdomadaire':
        prompt = f"""
        En tant qu'expert en gestion financière, analysez les statistiques hebdomadaires suivantes :

        **BUDGET: {stats['budget_nom']}**
        - Type de compte: {stats['compte_type']}
        - Devise: {stats['devise']}
        - Montant initial: {stats['montant_initial']}
        - Dépenses cette semaine: {stats['total_depenses']}
        - Entrées cette semaine: {stats['total_entrees']}
        - Solde actuel: {stats['solde_actuel']}
        - Taux d'utilisation: {stats['taux_utilisation']}%

        **DÉPENSES PAR CATÉGORIE:**
        """
        
        for cat in stats['categories']:
            prompt += f"\n- {cat['nom']}: {cat['montant_depense']}/{cat['montant_initial']} ({cat['pourcentage_utilise']}%)"
        
        prompt += f"""

        **CONSEILS DEMANDÉS:**
        1. Analyse de la gestion budgétaire
        2. Recommandations d'amélioration
        3. Conseils pour la semaine prochaine
        4. Alertes sur les risques potentiels

        Réponse en français, format structuré.
        """
    
    else:  # final
        prompt = f"""
        En tant qu'expert en gestion financière, analysez le bilan final de ce budget :

        **BILAN FINAL - BUDGET: {stats['budget_nom']}**
        - Type de compte: {stats['compte_type']}
        - Période: du {stats['date_debut']} au {stats['date_fin']}
        - Montant initial: {stats['montant_initial']}
        - Total dépenses: {stats['total_depenses']}
        - Total entrées: {stats['total_entrees']}
        - Solde final: {stats['solde_actuel']}
        - Taux d'utilisation: {stats['taux_utilisation']}%

        **PERFORMANCE PAR CATÉGORIE:**
        """
        
        for cat in stats['categories']:
            prompt += f"\n- {cat['nom']}: {cat['montant_depense']}/{cat['montant_initial']} ({cat['pourcentage_utilise']}%)"
        
        prompt += f"""

        **ANALYSE DEMANDÉE:**
        1. Bilan global de la gestion
        2. Points forts et points faibles
        3. Recommandations pour l'avenir
        4. Stratégies d'amélioration

        Réponse en français, format structuré.
        """
    
    # Appel à l'API Gemini
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    
    return response.text


@shared_task
def nettoyer_anciennes_notifications():
    """
    Nettoie les anciennes notifications (plus de 30 jours)
    """
    try:
        date_limite = timezone.now() - timedelta(days=30)
        count = Notification.objects.filter(
            created_at__lt=date_limite,
            viewed=True
        ).count()
        
        Notification.objects.filter(
            created_at__lt=date_limite,
            viewed=True
        ).delete()
        
        logger.info(f"{count} anciennes notifications supprimées")
        return f"{count} anciennes notifications supprimées"
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des notifications: {str(e)}")
        return f"Erreur: {str(e)}"


@shared_task
def rapport_quotidien_budgets():
    """
    Génère un rapport quotidien sur l'état des budgets
    """
    try:
        # Statistiques générales
        total_budgets_actifs = Budget.objects.filter(actif=True).count()
        budgets_expires_aujourd_hui = Budget.objects.filter(
            date_fin=timezone.now().date(),
            actif=True
        ).count()
        
        budgets_bientot_expires = Budget.objects.filter(
            date_fin__gte=timezone.now().date(),
            date_fin__lte=timezone.now().date() + timedelta(days=7),
            actif=True
        ).count()
        
        # Créer des notifications pour les budgets qui expirent bientôt
        budgets_bientot_expires_list = Budget.objects.filter(
            date_fin__gte=timezone.now().date(),
            date_fin__lte=timezone.now().date() + timedelta(days=7),
            actif=True
        ).select_related('user')
        
        for budget in budgets_bientot_expires_list:
            jours_restants = (budget.date_fin - timezone.now().date()).days
            Notification.objects.create(
                message=f"Attention: Votre budget '{budget.nom}' expire dans {jours_restants} jour(s)",
                type_notification='WARNING',
                user=budget.user
            )
        
        rapport = {
            'date': timezone.now().strftime('%Y-%m-%d'),
            'budgets_actifs': total_budgets_actifs,
            'budgets_expires_aujourd_hui': budgets_expires_aujourd_hui,
            'budgets_bientot_expires': budgets_bientot_expires,
            'notifications_creees': budgets_bientot_expires_list.count()
        }
        
        logger.info(f"Rapport quotidien généré: {rapport}")
        return f"Rapport quotidien généré: {rapport}"
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport quotidien: {str(e)}")
        return f"Erreur: {str(e)}"