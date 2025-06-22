#!/usr/bin/env python3
"""
Client de test pour l'application budgetManager de Optibudget
Teste tous les endpoints avec les en-têtes requis par le middleware
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta
import os
from typing import Dict, Any, Optional

class OptibudgetBudgetManagerClient:
    """Client pour tester l'API budgetManager de Optibudget"""
    
    def __init__(self, base_url: str = "http://localhost:8000", client_key: str = None, access_token: str = None):
        """
        Initialise le client
        
        Args:
            base_url: URL de base de l'API
            client_key: Clé client pour l'authentification (requise par le middleware)
            access_token: Token JWT pour l'authentification
        """
        self.base_url = base_url.rstrip('/')
        self.client_key = client_key
        self.access_token = access_token
        self.session = requests.Session()
        
        # Configuration des en-têtes par défaut
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Optibudget-TestClient/1.0',
        })
        
        # Ajouter la clé client si fournie
        if self.client_key:
            self.session.headers['X-Client-Key'] = self.client_key
        
        # Ajouter le token d'authentification si fourni
        if self.access_token:
            self.session.headers['Authorization'] = f'Bearer {self.access_token}'
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, 
                     requires_auth: bool = False) -> Dict[str, Any]:
        """
        Effectue une requête HTTP
        
        Args:
            method: Méthode HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint à appeler
            data: Données à envoyer
            requires_auth: Si l'authentification est requise
            
        Returns:
            Réponse de l'API
        """
        url = f"{self.base_url}/api/budget/{endpoint.lstrip('/')}"
        
        # Ajouter le token d'authentification si nécessaire
        headers = {}
        if requires_auth and self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Méthode HTTP non supportée: {method}")
            
            return {
                'status_code': response.status_code,
                'data': response.json() if response.content else {},
                'headers': dict(response.headers),
                'url': url
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'status_code': 0,
                'error': str(e),
                'url': url
            }
    
    def print_response(self, endpoint: str, response: Dict[str, Any]):
        """Affiche une réponse de manière formatée"""
        print(f"\n{'='*60}")
        print(f"🔗 {endpoint}")
        print(f"📊 Status: {response['status_code']}")
        print(f"🌐 URL: {response['url']}")
        
        if 'error' in response:
            print(f"❌ Erreur: {response['error']}")
        else:
            print(f"📄 Réponse: {json.dumps(response['data'], indent=2, ensure_ascii=False)}")
        print(f"{'='*60}")
    
    # ============================================================================
    # ENDPOINTS BUDGETS
    # ============================================================================
    
    def test_budgets_list(self) -> Dict[str, Any]:
        """Teste la liste des budgets"""
        print("\n💰 Test de liste des budgets...")
        response = self._make_request('GET', 'budgets/', requires_auth=True)
        self.print_response('GET /budgets/', response)
        return response
    
    def test_budget_create(self, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste la création d'un budget"""
        print("\n➕ Test de création de budget...")
        response = self._make_request('POST', 'budgets/', budget_data, requires_auth=True)
        self.print_response('POST /budgets/', response)
        return response
    
    def test_budget_detail(self, budget_id: str) -> Dict[str, Any]:
        """Teste les détails d'un budget"""
        print(f"\n📋 Test de détails du budget {budget_id[:20]}...")
        response = self._make_request('GET', f'budgets/{budget_id}/', requires_auth=True)
        self.print_response(f'GET /budgets/{budget_id[:20]}.../', response)
        return response
    
    def test_budget_update(self, budget_id: str, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste la mise à jour d'un budget"""
        print(f"\n✏️  Test de mise à jour du budget {budget_id[:20]}...")
        response = self._make_request('PUT', f'budgets/{budget_id}/', budget_data, requires_auth=True)
        self.print_response(f'PUT /budgets/{budget_id[:20]}.../', response)
        return response
    
    def test_budget_delete(self, budget_id: str) -> Dict[str, Any]:
        """Teste la suppression d'un budget"""
        print(f"\n🗑️  Test de suppression du budget {budget_id[:20]}...")
        response = self._make_request('DELETE', f'budgets/{budget_id}/', requires_auth=True)
        self.print_response(f'DELETE /budgets/{budget_id[:20]}.../', response)
        return response
    
    def test_budget_categories(self, budget_id: str) -> Dict[str, Any]:
        """Teste les catégories d'un budget"""
        print(f"\n📂 Test des catégories du budget {budget_id[:20]}...")
        response = self._make_request('GET', f'budgets/{budget_id}/categories/', requires_auth=True)
        self.print_response(f'GET /budgets/{budget_id[:20]}.../categories/', response)
        return response
    
    def test_budget_depenses(self, budget_id: str) -> Dict[str, Any]:
        """Teste les dépenses d'un budget"""
        print(f"\n💸 Test des dépenses du budget {budget_id[:20]}...")
        response = self._make_request('GET', f'budgets/{budget_id}/depenses/', requires_auth=True)
        self.print_response(f'GET /budgets/{budget_id[:20]}.../depenses/', response)
        return response
    
    def test_budget_resume(self, budget_id: str) -> Dict[str, Any]:
        """Teste le résumé d'un budget"""
        print(f"\n📊 Test du résumé du budget {budget_id[:20]}...")
        response = self._make_request('GET', f'budgets/{budget_id}/resume/', requires_auth=True)
        self.print_response(f'GET /budgets/{budget_id[:20]}.../resume/', response)
        return response
    
    def test_budget_export_csv(self, params: Dict[str, str] = None) -> Dict[str, Any]:
        """Teste l'export CSV des budgets"""
        print("\n📄 Test d'export CSV des budgets...")
        url = 'budgets/export_csv/'
        if params:
            url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        response = self._make_request('GET', url, requires_auth=True)
        self.print_response('GET /budgets/export_csv/', response)
        return response
    
    def test_budget_export_json(self, params: Dict[str, str] = None) -> Dict[str, Any]:
        """Teste l'export JSON des budgets"""
        print("\n📄 Test d'export JSON des budgets...")
        url = 'budgets/export_json/'
        if params:
            url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        response = self._make_request('GET', url, requires_auth=True)
        self.print_response('GET /budgets/export_json/', response)
        return response
    
    def test_budget_rapport_complet(self, params: Dict[str, str] = None) -> Dict[str, Any]:
        """Teste le rapport complet des budgets"""
        print("\n📈 Test du rapport complet des budgets...")
        url = 'budgets/rapport_complet/'
        if params:
            url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        response = self._make_request('GET', url, requires_auth=True)
        self.print_response('GET /budgets/rapport_complet/', response)
        return response
    
    # ============================================================================
    # ENDPOINTS CATÉGORIES DE DÉPENSES
    # ============================================================================
    
    def test_categories_list(self, budget_id: str = None) -> Dict[str, Any]:
        """Teste la liste des catégories"""
        print("\n📂 Test de liste des catégories...")
        url = 'categories-depense/'
        if budget_id:
            url += f'?budget_id={budget_id}'
        response = self._make_request('GET', url, requires_auth=True)
        self.print_response('GET /categories-depense/', response)
        return response
    
    def test_category_create(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste la création d'une catégorie"""
        print("\n➕ Test de création de catégorie...")
        response = self._make_request('POST', 'categories-depense/', category_data, requires_auth=True)
        self.print_response('POST /categories-depense/', response)
        return response
    
    def test_category_detail(self, category_id: str) -> Dict[str, Any]:
        """Teste les détails d'une catégorie"""
        print(f"\n📋 Test de détails de la catégorie {category_id[:20]}...")
        response = self._make_request('GET', f'categories-depense/{category_id}/', requires_auth=True)
        self.print_response(f'GET /categories-depense/{category_id[:20]}.../', response)
        return response
    
    def test_category_update(self, category_id: str, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste la mise à jour d'une catégorie"""
        print(f"\n✏️  Test de mise à jour de la catégorie {category_id[:20]}...")
        response = self._make_request('PUT', f'categories-depense/{category_id}/', category_data, requires_auth=True)
        self.print_response(f'PUT /categories-depense/{category_id[:20]}.../', response)
        return response
    
    def test_category_delete(self, category_id: str) -> Dict[str, Any]:
        """Teste la suppression d'une catégorie"""
        print(f"\n🗑️  Test de suppression de la catégorie {category_id[:20]}...")
        response = self._make_request('DELETE', f'categories-depense/{category_id}/', requires_auth=True)
        self.print_response(f'DELETE /categories-depense/{category_id[:20]}.../', response)
        return response
    
    def test_category_depenses(self, category_id: str) -> Dict[str, Any]:
        """Teste les dépenses d'une catégorie"""
        print(f"\n💸 Test des dépenses de la catégorie {category_id[:20]}...")
        response = self._make_request('GET', f'categories-depense/{category_id}/depenses/', requires_auth=True)
        self.print_response(f'GET /categories-depense/{category_id[:20]}.../depenses/', response)
        return response
    
    def test_category_stats(self, category_id: str) -> Dict[str, Any]:
        """Teste les statistiques d'une catégorie"""
        print(f"\n📊 Test des statistiques de la catégorie {category_id[:20]}...")
        response = self._make_request('GET', f'categories-depense/{category_id}/stats/', requires_auth=True)
        self.print_response(f'GET /categories-depense/{category_id[:20]}.../stats/', response)
        return response
    
    def test_categories_stats_globales(self) -> Dict[str, Any]:
        """Teste les statistiques globales des catégories"""
        print("\n📊 Test des statistiques globales des catégories...")
        response = self._make_request('GET', 'categories-depense/stats-globales/', requires_auth=True)
        self.print_response('GET /categories-depense/stats-globales/', response)
        return response
    
    # ============================================================================
    # ENDPOINTS DÉPENSES
    # ============================================================================
    
    def test_depenses_list(self, budget_id: str = None) -> Dict[str, Any]:
        """Teste la liste des dépenses"""
        print("\n💸 Test de liste des dépenses...")
        url = 'depenses/'
        if budget_id:
            url += f'?budget_id={budget_id}'
        response = self._make_request('GET', url, requires_auth=True)
        self.print_response('GET /depenses/', response)
        return response
    
    def test_depense_create(self, depense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste la création d'une dépense"""
        print("\n➕ Test de création de dépense...")
        response = self._make_request('POST', 'depenses/', depense_data, requires_auth=True)
        self.print_response('POST /depenses/', response)
        return response
    
    def test_depense_detail(self, depense_id: str) -> Dict[str, Any]:
        """Teste les détails d'une dépense"""
        print(f"\n📋 Test de détails de la dépense {depense_id[:20]}...")
        response = self._make_request('GET', f'depenses/{depense_id}/', requires_auth=True)
        self.print_response(f'GET /depenses/{depense_id[:20]}.../', response)
        return response
    
    def test_depense_update(self, depense_id: str, depense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste la mise à jour d'une dépense"""
        print(f"\n✏️  Test de mise à jour de la dépense {depense_id[:20]}...")
        response = self._make_request('PUT', f'depenses/{depense_id}/', depense_data, requires_auth=True)
        self.print_response(f'PUT /depenses/{depense_id[:20]}.../', response)
        return response
    
    def test_depense_delete(self, depense_id: str) -> Dict[str, Any]:
        """Teste la suppression d'une dépense"""
        print(f"\n🗑️  Test de suppression de la dépense {depense_id[:20]}...")
        response = self._make_request('DELETE', f'depenses/{depense_id}/', requires_auth=True)
        self.print_response(f'DELETE /depenses/{depense_id[:20]}.../', response)
        return response
    
    # ============================================================================
    # ENDPOINTS ENTREPRISE (Entrées, Employés, Paiements, Salaires)
    # ============================================================================
    
    def test_entrees_list(self, budget_id: str = None) -> Dict[str, Any]:
        """Teste la liste des entrées (entreprise uniquement)"""
        print("\n💰 Test de liste des entrées (entreprise)...")
        url = 'entrees/'
        if budget_id:
            url += f'?budget_id={budget_id}'
        response = self._make_request('GET', url, requires_auth=True)
        self.print_response('GET /entrees/', response)
        return response
    
    def test_entree_create(self, entree_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste la création d'une entrée (entreprise uniquement)"""
        print("\n➕ Test de création d'entrée (entreprise)...")
        response = self._make_request('POST', 'entrees/', entree_data, requires_auth=True)
        self.print_response('POST /entrees/', response)
        return response
    
    def test_entrees_statistiques(self) -> Dict[str, Any]:
        """Teste les statistiques des entrées (entreprise uniquement)"""
        print("\n📊 Test des statistiques des entrées (entreprise)...")
        response = self._make_request('GET', 'entrees/statistiques/', requires_auth=True)
        self.print_response('GET /entrees/statistiques/', response)
        return response
    
    def test_employes_list(self) -> Dict[str, Any]:
        """Teste la liste des employés (entreprise uniquement)"""
        print("\n👥 Test de liste des employés (entreprise)...")
        response = self._make_request('GET', 'employes/', requires_auth=True)
        self.print_response('GET /employes/', response)
        return response
    
    def test_employe_create(self, employe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste la création d'un employé (entreprise uniquement)"""
        print("\n➕ Test de création d'employé (entreprise)...")
        response = self._make_request('POST', 'employes/', employe_data, requires_auth=True)
        self.print_response('POST /employes/', response)
        return response
    
    def test_employe_detail(self, employe_id: str) -> Dict[str, Any]:
        """Teste les détails d'un employé (entreprise uniquement)"""
        print(f"\n📋 Test de détails de l'employé {employe_id[:20]}...")
        response = self._make_request('GET', f'employes/{employe_id}/', requires_auth=True)
        self.print_response(f'GET /employes/{employe_id[:20]}.../', response)
        return response
    
    def test_employe_paiements(self, employe_id: str) -> Dict[str, Any]:
        """Teste les paiements d'un employé (entreprise uniquement)"""
        print(f"\n💳 Test des paiements de l'employé {employe_id[:20]}...")
        response = self._make_request('GET', f'employes/{employe_id}/paiements/', requires_auth=True)
        self.print_response(f'GET /employes/{employe_id[:20]}.../paiements/', response)
        return response
    
    def test_employes_par_statut(self, statut: str) -> Dict[str, Any]:
        """Teste les employés par statut (entreprise uniquement)"""
        print(f"\n👥 Test des employés par statut: {statut}...")
        response = self._make_request('GET', f'employes/par_statut/{statut}/', requires_auth=True)
        self.print_response(f'GET /employes/par_statut/{statut}/', response)
        return response
    
    def test_employes_actifs(self) -> Dict[str, Any]:
        """Teste les employés actifs (entreprise uniquement)"""
        print("\n👥 Test des employés actifs (entreprise)...")
        response = self._make_request('GET', 'employes/actifs/', requires_auth=True)
        self.print_response('GET /employes/actifs/', response)
        return response
    
    def test_employes_export_csv(self) -> Dict[str, Any]:
        """Teste l'export CSV des employés (entreprise uniquement)"""
        print("\n📄 Test d'export CSV des employés (entreprise)...")
        response = self._make_request('GET', 'employes/export_csv/', requires_auth=True)
        self.print_response('GET /employes/export_csv/', response)
        return response
    
    def test_employes_rapport_complet(self) -> Dict[str, Any]:
        """Teste le rapport complet des employés (entreprise uniquement)"""
        print("\n📈 Test du rapport complet des employés (entreprise)...")
        response = self._make_request('GET', 'employes/rapport_complet/', requires_auth=True)
        self.print_response('GET /employes/rapport_complet/', response)
        return response
    
    def test_paiements_employes_list(self) -> Dict[str, Any]:
        """Teste la liste des paiements d'employés (entreprise uniquement)"""
        print("\n💳 Test de liste des paiements d'employés (entreprise)...")
        response = self._make_request('GET', 'paiements-employes/', requires_auth=True)
        self.print_response('GET /paiements-employes/', response)
        return response
    
    def test_paiement_employe_create(self, paiement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste la création d'un paiement d'employé (entreprise uniquement)"""
        print("\n➕ Test de création de paiement d'employé (entreprise)...")
        response = self._make_request('POST', 'paiements-employes/', paiement_data, requires_auth=True)
        self.print_response('POST /paiements-employes/', response)
        return response
    
    def test_paiement_global(self, paiement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste le paiement global (entreprise uniquement)"""
        print("\n💳 Test de paiement global (entreprise)...")
        response = self._make_request('POST', 'paiements-employes/paiement-global/', paiement_data, requires_auth=True)
        self.print_response('POST /paiements-employes/paiement-global/', response)
        return response
    
    def test_preview_paiement_global(self) -> Dict[str, Any]:
        """Teste l'aperçu du paiement global (entreprise uniquement)"""
        print("\n👁️  Test d'aperçu du paiement global (entreprise)...")
        response = self._make_request('GET', 'paiements-employes/preview-paiement-global/', requires_auth=True)
        self.print_response('GET /paiements-employes/preview-paiement-global/', response)
        return response
    
    def test_paiements_statistiques(self) -> Dict[str, Any]:
        """Teste les statistiques des paiements (entreprise uniquement)"""
        print("\n📊 Test des statistiques des paiements (entreprise)...")
        response = self._make_request('GET', 'paiements-employes/statistiques/', requires_auth=True)
        self.print_response('GET /paiements-employes/statistiques/', response)
        return response
    
    def test_paiements_par_employe(self) -> Dict[str, Any]:
        """Teste les paiements par employé (entreprise uniquement)"""
        print("\n👥 Test des paiements par employé (entreprise)...")
        response = self._make_request('GET', 'paiements-employes/par-employe/', requires_auth=True)
        self.print_response('GET /paiements-employes/par-employe/', response)
        return response
    
    def test_montants_salaire_list(self) -> Dict[str, Any]:
        """Teste la liste des montants de salaire (entreprise uniquement)"""
        print("\n💰 Test de liste des montants de salaire (entreprise)...")
        response = self._make_request('GET', 'montants-salaire/', requires_auth=True)
        self.print_response('GET /montants-salaire/', response)
        return response
    
    def test_montant_salaire_create(self, salaire_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste la création d'un montant de salaire (entreprise uniquement)"""
        print("\n➕ Test de création de montant de salaire (entreprise)...")
        response = self._make_request('POST', 'montants-salaire/', salaire_data, requires_auth=True)
        self.print_response('POST /montants-salaire/', response)
        return response
    
    def test_montant_salaire_calculer(self, calcul_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste le calcul de salaire (entreprise uniquement)"""
        print("\n🧮 Test de calcul de salaire (entreprise)...")
        response = self._make_request('POST', 'montants-salaire/calculer/', calcul_data, requires_auth=True)
        self.print_response('POST /montants-salaire/calculer/', response)
        return response
    
    # ============================================================================
    # ENDPOINTS NOTIFICATIONS ET CONSEILS
    # ============================================================================
    
    def test_notifications_list(self) -> Dict[str, Any]:
        """Teste la liste des notifications"""
        print("\n🔔 Test de liste des notifications...")
        response = self._make_request('GET', 'notifications/', requires_auth=True)
        self.print_response('GET /notifications/', response)
        return response
    
    def test_notifications_non_lues(self) -> Dict[str, Any]:
        """Teste les notifications non lues"""
        print("\n🔔 Test des notifications non lues...")
        response = self._make_request('GET', 'notifications/non-lues/', requires_auth=True)
        self.print_response('GET /notifications/non-lues/', response)
        return response
    
    def test_notifications_marquer_toutes_lues(self) -> Dict[str, Any]:
        """Teste le marquage de toutes les notifications comme lues"""
        print("\n✅ Test de marquage de toutes les notifications comme lues...")
        response = self._make_request('POST', 'notifications/marquer-toutes-lues/', requires_auth=True)
        self.print_response('POST /notifications/marquer-toutes-lues/', response)
        return response
    
    def test_conseils_list(self) -> Dict[str, Any]:
        """Teste la liste des conseils"""
        print("\n💡 Test de liste des conseils...")
        response = self._make_request('GET', 'conseils/', requires_auth=True)
        self.print_response('GET /conseils/', response)
        return response
    
    def test_conseils_recents(self) -> Dict[str, Any]:
        """Teste les conseils récents"""
        print("\n💡 Test des conseils récents...")
        response = self._make_request('GET', 'conseils/recents/', requires_auth=True)
        self.print_response('GET /conseils/recents/', response)
        return response
    
    # ============================================================================
    # ENDPOINTS DE STATISTIQUES ET RAPPORTS
    # ============================================================================
    
    def test_budget_statistics(self, budget_id: str) -> Dict[str, Any]:
        """Teste les statistiques d'un budget"""
        print(f"\n📊 Test des statistiques du budget {budget_id[:20]}...")
        response = self._make_request('GET', f'budgets/{budget_id}/statistiques/', requires_auth=True)
        self.print_response(f'GET /budgets/{budget_id[:20]}.../statistiques/', response)
        return response
    
    def test_all_budgets_statistics(self) -> Dict[str, Any]:
        """Teste les statistiques de tous les budgets"""
        print("\n📊 Test des statistiques de tous les budgets...")
        response = self._make_request('GET', 'budgets/statistiques-globales/', requires_auth=True)
        self.print_response('GET /budgets/statistiques-globales/', response)
        return response
    
    def test_category_statistics(self, category_id: str) -> Dict[str, Any]:
        """Teste les statistiques d'une catégorie"""
        print(f"\n📊 Test des statistiques de la catégorie {category_id[:20]}...")
        response = self._make_request('GET', f'categories/{category_id}/statistiques/', requires_auth=True)
        self.print_response(f'GET /categories/{category_id[:20]}.../statistiques/', response)
        return response
    
    def test_global_financial_report(self) -> Dict[str, Any]:
        """Teste le rapport financier global"""
        print("\n📈 Test du rapport financier global...")
        response = self._make_request('GET', 'rapport-financier-global/', requires_auth=True)
        self.print_response('GET /rapport-financier-global/', response)
        return response
    
    def test_conseils_par_type(self) -> Dict[str, Any]:
        """Teste les conseils par type de compte"""
        print("\n💡 Test des conseils par type de compte...")
        response = self._make_request('GET', 'test-conseils/', requires_auth=True)
        self.print_response('GET /test-conseils/', response)
        return response
    
    # ============================================================================
    # TESTS COMPLETS
    # ============================================================================
    
    def run_complete_test(self):
        """Exécute une suite complète de tests"""
        print("🚀 Démarrage des tests complets de l'API budgetManager")
        print("=" * 80)
        
        # Données de test
        test_budget_data = {
            "nom": f"Budget Test {int(time.time())}",
            "montant": 10000.0,
            "montant_initial": 10000.0,
            "date_fin": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            "description": "Budget de test pour les tests API",
            "type_budget": "D"
        }
        
        test_category_data = {
            "nom": f"Catégorie Test {int(time.time())}",
            "description": "Catégorie de test",
            "montant": 1000.0,
            "montant_initial": 1000.0
        }
        
        test_depense_data = {
            "nom": f"Dépense Test {int(time.time())}",
            "montant": 100.0,
            "type_depense": "DP",
            "description": "Dépense de test"
        }
        
        # 1. Tests des budgets
        print("\n💰 PHASE 1: Tests des budgets")
        print("-" * 50)
        
        # Liste des budgets
        self.test_budgets_list()
        
        # Création d'un budget
        budget_response = self.test_budget_create(test_budget_data)
        
        if budget_response['status_code'] != 201:
            print("❌ Échec de la création du budget, arrêt des tests")
            return
        
        budget_id = budget_response['data'].get('id')
        
        # Détails du budget
        self.test_budget_detail(budget_id)
        
        # Résumé du budget
        self.test_budget_resume(budget_id)
        
        # 2. Tests des catégories
        print("\n📂 PHASE 2: Tests des catégories")
        print("-" * 50)
        
        # Ajouter le budget_id aux données de catégorie
        test_category_data['id_budget'] = budget_id
        
        # Liste des catégories
        self.test_categories_list(budget_id)
        
        # Création d'une catégorie
        category_response = self.test_category_create(test_category_data)
        
        if category_response['status_code'] == 201:
            category_id = category_response['data'].get('id')
            
            # Détails de la catégorie
            self.test_category_detail(category_id)
            
            # Statistiques de la catégorie
            self.test_category_stats(category_id)
        
        # Statistiques globales des catégories
        self.test_categories_stats_globales()
        
        # 3. Tests des dépenses
        print("\n💸 PHASE 3: Tests des dépenses")
        print("-" * 50)
        
        # Ajouter les IDs aux données de dépense
        test_depense_data['id_budget'] = budget_id
        if category_response['status_code'] == 201:
            test_depense_data['id_cat_depense'] = category_id
        
        # Liste des dépenses
        self.test_depenses_list(budget_id)
        
        # Création d'une dépense
        depense_response = self.test_depense_create(test_depense_data)
        
        if depense_response['status_code'] == 201:
            depense_id = depense_response['data'].get('id')
            
            # Détails de la dépense
            self.test_depense_detail(depense_id)
        
        # Dépenses du budget
        self.test_budget_depenses(budget_id)
        
        # 4. Tests des notifications et conseils
        print("\n🔔 PHASE 4: Tests des notifications et conseils")
        print("-" * 50)
        
        self.test_notifications_list()
        self.test_notifications_non_lues()
        self.test_conseils_list()
        self.test_conseils_recents()
        
        # 5. Tests des statistiques et rapports
        print("\n📊 PHASE 5: Tests des statistiques et rapports")
        print("-" * 50)
        
        self.test_budget_statistics(budget_id)
        self.test_all_budgets_statistics()
        self.test_global_financial_report()
        self.test_conseils_par_type()
        
        # 6. Tests d'export
        print("\n📄 PHASE 6: Tests d'export")
        print("-" * 50)
        
        self.test_budget_export_csv()
        self.test_budget_export_json()
        self.test_budget_rapport_complet()
        
        # 7. Tests entreprise (si applicable)
        print("\n🏢 PHASE 7: Tests entreprise")
        print("-" * 50)
        
        # Ces tests peuvent échouer si l'utilisateur n'est pas de type entreprise
        self.test_entrees_list()
        self.test_employes_list()
        self.test_paiements_employes_list()
        self.test_montants_salaire_list()
        
        print("\n✅ Tests complets terminés!")
    
    def run_entreprise_test(self):
        """Exécute des tests spécifiques aux comptes entreprise"""
        print("🏢 Démarrage des tests entreprise")
        print("=" * 80)
        
        # Données de test entreprise
        test_entree_data = {
            "nom": f"Entrée Test {int(time.time())}",
            "montant": 5000.0,
            "description": "Entrée de test pour entreprise"
        }
        
        test_employe_data = {
            "nom": "Doe",
            "prenom": "John",
            "telephone": "+237123456789",
            "email": "john.doe@test.com",
            "type_employe": "EMP",
            "poste": "Développeur"
        }
        
        test_paiement_data = {
            "montant": 1000.0,
            "type_paiement": "SALAIRE",
            "description": "Paiement de test"
        }
        
        test_salaire_data = {
            "salaire_direction": 5000.0,
            "salaire_cadre": 3000.0,
            "salaire_employe": 2000.0,
            "salaire_ouvrier": 1500.0,
            "salaire_cf": 2500.0,
            "salaire_stagiaire": 800.0,
            "salaire_intermediaire": 1200.0,
            "salaire_autre": 1000.0
        }
        
        # Tests des entrées
        print("\n💰 Tests des entrées")
        print("-" * 30)
        self.test_entrees_list()
        self.test_entree_create(test_entree_data)
        self.test_entrees_statistiques()
        
        # Tests des employés
        print("\n👥 Tests des employés")
        print("-" * 30)
        self.test_employes_list()
        employe_response = self.test_employe_create(test_employe_data)
        
        if employe_response['status_code'] == 201:
            employe_id = employe_response['data'].get('id')
            self.test_employe_detail(employe_id)
            self.test_employe_paiements(employe_id)
        
        self.test_employes_actifs()
        self.test_employes_par_statut("ES")
        self.test_employes_export_csv()
        self.test_employes_rapport_complet()
        
        # Tests des paiements
        print("\n💳 Tests des paiements")
        print("-" * 30)
        self.test_paiements_employes_list()
        self.test_preview_paiement_global()
        self.test_paiements_statistiques()
        self.test_paiements_par_employe()
        
        # Tests des salaires
        print("\n💰 Tests des salaires")
        print("-" * 30)
        self.test_montants_salaire_list()
        self.test_montant_salaire_create(test_salaire_data)
        self.test_montant_salaire_calculer({
            "type_employe": "EMP",
            "periode": "mensuel"
        })
        
        print("\n✅ Tests entreprise terminés!")


def main():
    """Fonction principale pour exécuter les tests"""
    print("🧪 Client de test pour l'API budgetManager Optibudget")
    print("=" * 60)
    
    # Configuration
    base_url = input("🌐 URL de base (défaut: http://localhost:8000): ").strip() or "http://localhost:8000"
    client_key = input("🔑 Clé client (optionnel): ").strip() or None
    access_token = input("🔐 Token d'accès JWT (requis): ").strip()
    
    if not access_token:
        print("❌ Token d'accès requis pour tester l'API budgetManager")
        return
    
    # Création du client
    client = OptibudgetBudgetManagerClient(base_url, client_key, access_token)
    
    print(f"\n🔧 Configuration:")
    print(f"   URL: {base_url}")
    print(f"   Clé client: {'✅ Fournie' if client_key else '❌ Non fournie'}")
    print(f"   Token JWT: {'✅ Fourni' if access_token else '❌ Non fourni'}")
    
    # Menu de choix
    while True:
        print("\n" + "=" * 50)
        print("📋 MENU DE TESTS BUDGETMANAGER")
        print("=" * 50)
        print("1. 🚀 Tests complets")
        print("2. 🏢 Tests entreprise")
        print("3. 💰 Test des budgets")
        print("4. 📂 Test des catégories")
        print("5. 💸 Test des dépenses")
        print("6. 🏢 Test des fonctionnalités entreprise")
        print("7. 🔔 Test des notifications")
        print("8. 📊 Test des statistiques")
        print("0. ❌ Quitter")
        
        choice = input("\n🎯 Votre choix: ").strip()
        
        if choice == "1":
            client.run_complete_test()
        elif choice == "2":
            client.run_entreprise_test()
        elif choice == "3":
            client.test_budgets_list()
        elif choice == "4":
            client.test_categories_list()
        elif choice == "5":
            client.test_depenses_list()
        elif choice == "6":
            client.run_entreprise_test()
        elif choice == "7":
            client.test_notifications_list()
            client.test_conseils_list()
        elif choice == "8":
            client.test_all_budgets_statistics()
            client.test_global_financial_report()
        elif choice == "0":
            print("👋 Au revoir!")
            break
        else:
            print("❌ Choix invalide")


if __name__ == "__main__":
    main()
