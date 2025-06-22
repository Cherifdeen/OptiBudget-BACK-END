"""
Module pour la génération de rapports et exports de données
"""
import csv
import json
from io import StringIO
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from .models import Budget, CategorieDepense, Depense, Entree, Employe, PaiementEmploye, MontantSalaire


class BudgetReportGenerator:
    """Générateur de rapports pour les budgets"""
    
    def __init__(self, user):
        self.user = user
    
    def generate_budget_summary(self, budget_id=None, date_debut=None, date_fin=None):
        """Générer un résumé de budget"""
        if budget_id:
            budgets = Budget.objects.filter(id=budget_id, user=self.user)
        else:
            budgets = Budget.objects.filter(user=self.user)
        
        if date_debut and date_fin:
            budgets = budgets.filter(created_at__date__range=[date_debut, date_fin])
        
        summary = {
            'periode': {
                'debut': date_debut.isoformat() if date_debut else None,
                'fin': date_fin.isoformat() if date_fin else None
            },
            'budgets': [],
            'totaux': {
                'montant_initial_total': 0,
                'montant_restant_total': 0,
                'montant_utilise_total': 0,
                'nombre_budgets': 0
            }
        }
        
        for budget in budgets:
            budget_data = {
                'id': str(budget.id),
                'nom': budget.nom,
                'montant_initial': budget.montant_initial,
                'montant_restant': budget.montant,
                'montant_utilise': budget.get_montant_utilise(),
                'pourcentage_utilise': budget.get_pourcentage_utilise(),
                'date_creation': budget.created_at.isoformat(),
                'date_fin': budget.date_fin.isoformat() if budget.date_fin else None,
                'type_budget': budget.get_type_budget_display(),
                'actif': budget.actif,
                'categories': self._get_categories_summary(budget),
                'depenses': self._get_depenses_summary(budget),
                'entrees': self._get_entrees_summary(budget) if self.user.compte == 'entreprise' else [],
                'paiements_employes': self._get_paiements_summary(budget) if self.user.compte == 'entreprise' else []
            }
            
            summary['budgets'].append(budget_data)
            summary['totaux']['montant_initial_total'] += budget.montant_initial
            summary['totaux']['montant_restant_total'] += budget.montant
            summary['totaux']['montant_utilise_total'] += budget.get_montant_utilise()
            summary['totaux']['nombre_budgets'] += 1
        
        return summary
    
    def _get_categories_summary(self, budget):
        """Obtenir le résumé des catégories d'un budget"""
        categories = CategorieDepense.objects.filter(id_budget=budget)
        return [{
            'nom': cat.nom,
            'montant_initial': cat.montant_initial,
            'montant_restant': cat.montant,
            'montant_utilise': cat.montant_initial - cat.montant,
            'pourcentage_utilise': round(((cat.montant_initial - cat.montant) / cat.montant_initial) * 100, 2) if cat.montant_initial > 0 else 0
        } for cat in categories]
    
    def _get_depenses_summary(self, budget):
        """Obtenir le résumé des dépenses d'un budget"""
        depenses = Depense.objects.filter(id_budget=budget)
        return [{
            'nom': dep.nom,
            'montant': dep.montant,
            'type': dep.get_type_depense_display(),
            'categorie': dep.id_cat_depense.nom if dep.id_cat_depense else 'Aucune',
            'date': dep.created_at.isoformat(),
            'description': dep.description
        } for dep in depenses]
    
    def _get_entrees_summary(self, budget):
        """Obtenir le résumé des entrées d'un budget"""
        entrees = Entree.objects.filter(id_budget=budget)
        return [{
            'nom': ent.nom,
            'montant': ent.montant,
            'date': ent.created_at.isoformat(),
            'description': ent.description
        } for ent in entrees]
    
    def _get_paiements_summary(self, budget):
        """Obtenir le résumé des paiements d'employés d'un budget"""
        paiements = PaiementEmploye.objects.filter(id_budget=budget)
        return [{
            'employe': f"{paiement.id_employe.nom} {paiement.id_employe.prenom}",
            'montant': paiement.montant,
            'type': paiement.type_paiement,
            'date': paiement.date_paiement.isoformat(),
            'description': paiement.description
        } for paiement in paiements]
    
    def export_to_csv(self, budget_id=None, date_debut=None, date_fin=None):
        """Exporter les données de budget en CSV"""
        summary = self.generate_budget_summary(budget_id, date_debut, date_fin)
        
        # Créer le fichier CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="budget_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # En-têtes
        writer.writerow(['RAPPORT BUDGET - Optibudget'])
        writer.writerow(['Généré le:', datetime.now().strftime("%d/%m/%Y %H:%M")])
        writer.writerow(['Utilisateur:', self.user.email])
        writer.writerow([])
        
        # Totaux
        writer.writerow(['TOTAUX GÉNÉRAUX'])
        writer.writerow(['Nombre de budgets:', summary['totaux']['nombre_budgets']])
        writer.writerow(['Montant initial total:', f"{summary['totaux']['montant_initial_total']:.2f} €"])
        writer.writerow(['Montant restant total:', f"{summary['totaux']['montant_restant_total']:.2f} €"])
        writer.writerow(['Montant utilisé total:', f"{summary['totaux']['montant_utilise_total']:.2f} €"])
        writer.writerow([])
        
        # Détails par budget
        for budget in summary['budgets']:
            writer.writerow([f"BUDGET: {budget['nom']}"])
            writer.writerow(['Montant initial:', f"{budget['montant_initial']:.2f} €"])
            writer.writerow(['Montant restant:', f"{budget['montant_restant']:.2f} €"])
            writer.writerow(['Montant utilisé:', f"{budget['montant_utilise']:.2f} €"])
            writer.writerow(['Pourcentage utilisé:', f"{budget['pourcentage_utilise']:.2f}%"])
            writer.writerow(['Type:', budget['type_budget']])
            writer.writerow(['Statut:', 'Actif' if budget['actif'] else 'Inactif'])
            writer.writerow([])
            
            # Catégories
            if budget['categories']:
                writer.writerow(['CATÉGORIES'])
                writer.writerow(['Nom', 'Montant initial', 'Montant restant', 'Montant utilisé', 'Pourcentage utilisé'])
                for cat in budget['categories']:
                    writer.writerow([
                        cat['nom'],
                        f"{cat['montant_initial']:.2f} €",
                        f"{cat['montant_restant']:.2f} €",
                        f"{cat['montant_utilise']:.2f} €",
                        f"{cat['pourcentage_utilise']:.2f}%"
                    ])
                writer.writerow([])
            
            # Dépenses
            if budget['depenses']:
                writer.writerow(['DÉPENSES'])
                writer.writerow(['Nom', 'Montant', 'Type', 'Catégorie', 'Date', 'Description'])
                for dep in budget['depenses']:
                    writer.writerow([
                        dep['nom'],
                        f"{dep['montant']:.2f} €",
                        dep['type'],
                        dep['categorie'],
                        dep['date'][:10],
                        dep['description'] or ''
                    ])
                writer.writerow([])
            
            # Entrées (entreprise uniquement)
            if budget['entrees'] and self.user.compte == 'entreprise':
                writer.writerow(['ENTRÉES'])
                writer.writerow(['Nom', 'Montant', 'Date', 'Description'])
                for ent in budget['entrees']:
                    writer.writerow([
                        ent['nom'],
                        f"{ent['montant']:.2f} €",
                        ent['date'][:10],
                        ent['description'] or ''
                    ])
                writer.writerow([])
            
            # Paiements employés (entreprise uniquement)
            if budget['paiements_employes'] and self.user.compte == 'entreprise':
                writer.writerow(['PAIEMENTS EMPLOYÉS'])
                writer.writerow(['Employé', 'Montant', 'Type', 'Date', 'Description'])
                for paiement in budget['paiements_employes']:
                    writer.writerow([
                        paiement['employe'],
                        f"{paiement['montant']:.2f} €",
                        paiement['type'],
                        paiement['date'][:10],
                        paiement['description'] or ''
                    ])
                writer.writerow([])
            
            writer.writerow(['=' * 50])
            writer.writerow([])
        
        return response
    
    def export_to_json(self, budget_id=None, date_debut=None, date_fin=None):
        """Exporter les données de budget en JSON"""
        summary = self.generate_budget_summary(budget_id, date_debut, date_fin)
        
        response = HttpResponse(
            json.dumps(summary, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="budget_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        
        return response


class EmployeReportGenerator:
    """Générateur de rapports pour les employés (entreprise uniquement)"""
    
    def __init__(self, user):
        if user.compte != 'entreprise':
            raise ValueError("Les rapports employés ne sont disponibles que pour les comptes entreprise")
        self.user = user
    
    def generate_employe_summary(self, date_debut=None, date_fin=None):
        """Générer un résumé des employés"""
        employes = Employe.objects.filter(user=self.user)
        
        if date_debut and date_fin:
            # Filtrer par date de prise de service
            employes = employes.filter(prise_service__date__range=[date_debut, date_fin])
        
        summary = {
            'periode': {
                'debut': date_debut.isoformat() if date_debut else None,
                'fin': date_fin.isoformat() if date_fin else None
            },
            'employes': [],
            'statistiques': {
                'total_employes': 0,
                'employes_actifs': 0,
                'employes_en_conge': 0,
                'employes_retraites': 0,
                'employes_licencies': 0,
                'total_salaires_mensuel': 0
            }
        }
        
        for employe in employes:
            # Calculer le salaire total de l'employé
            montant_salaire = MontantSalaire.objects.filter(user=self.user).first()
            salaire_total = 0
            if montant_salaire:
                salaire_total = montant_salaire.get_total_by_type(employe.type_employe)
            
            employe_data = {
                'id': str(employe.id),
                'nom': employe.nom,
                'prenom': employe.prenom,
                'email': employe.email,
                'telephone': employe.telephone,
                'type_employe': employe.get_type_employe_display(),
                'poste': employe.poste,
                'statut': employe.get_actif_display(),
                'date_naissance': employe.date_naissance.isoformat() if employe.date_naissance else None,
                'prise_service': employe.prise_service.isoformat() if employe.prise_service else None,
                'salaire_mensuel': salaire_total,
                'paiements': self._get_paiements_employe(employe)
            }
            
            summary['employes'].append(employe_data)
            
            # Mettre à jour les statistiques
            summary['statistiques']['total_employes'] += 1
            summary['statistiques']['total_salaires_mensuel'] += salaire_total
            
            if employe.actif == 'ES':
                summary['statistiques']['employes_actifs'] += 1
            elif employe.actif == 'EC':
                summary['statistiques']['employes_en_conge'] += 1
            elif employe.actif == 'ER':
                summary['statistiques']['employes_retraites'] += 1
            elif employe.actif == 'LC':
                summary['statistiques']['employes_licencies'] += 1
        
        return summary
    
    def _get_paiements_employe(self, employe):
        """Obtenir les paiements d'un employé"""
        paiements = PaiementEmploye.objects.filter(id_employe=employe)
        return [{
            'montant': paiement.montant,
            'type': paiement.type_paiement,
            'date': paiement.date_paiement.isoformat(),
            'budget': paiement.id_budget.nom,
            'description': paiement.description
        } for paiement in paiements]
    
    def export_to_csv(self, date_debut=None, date_fin=None):
        """Exporter les données d'employés en CSV"""
        summary = self.generate_employe_summary(date_debut, date_fin)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="employe_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # En-têtes
        writer.writerow(['RAPPORT EMPLOYÉS - Optibudget'])
        writer.writerow(['Généré le:', datetime.now().strftime("%d/%m/%Y %H:%M")])
        writer.writerow(['Utilisateur:', self.user.email])
        writer.writerow([])
        
        # Statistiques
        stats = summary['statistiques']
        writer.writerow(['STATISTIQUES'])
        writer.writerow(['Total employés:', stats['total_employes']])
        writer.writerow(['Employés actifs:', stats['employes_actifs']])
        writer.writerow(['Employés en congé:', stats['employes_en_conge']])
        writer.writerow(['Employés retraités:', stats['employes_retraites']])
        writer.writerow(['Employés licenciés:', stats['employes_licencies']])
        writer.writerow(['Total salaires mensuel:', f"{stats['total_salaires_mensuel']:.2f} €"])
        writer.writerow([])
        
        # Détails des employés
        writer.writerow(['DÉTAILS DES EMPLOYÉS'])
        writer.writerow(['Nom', 'Prénom', 'Email', 'Téléphone', 'Type', 'Poste', 'Statut', 'Salaire mensuel'])
        
        for employe in summary['employes']:
            writer.writerow([
                employe['nom'],
                employe['prenom'],
                employe['email'] or '',
                employe['telephone'],
                employe['type_employe'],
                employe['poste'],
                employe['statut'],
                f"{employe['salaire_mensuel']:.2f} €"
            ])
        
        return response 