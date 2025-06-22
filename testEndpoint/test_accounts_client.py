#!/usr/bin/env python3
"""
Client de test pour l'application accounts de Optibudget
Teste tous les endpoints avec les en-têtes requis par le middleware
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta
import os
from typing import Dict, Any, Optional

class OptibudgetAccountsClient:
    """Client pour tester l'API accounts de Optibudget"""
    
    def __init__(self, base_url: str = "http://localhost:8000", client_key: str = None, access_token: str = None):
        """
        Initialise le client
        
        Args:
            base_url: URL de base de l'API
            client_key: Clé client pour l'authentification (requise par le middleware)
            access_token: Token d'accès pour les requêtes authentifiées
        """
        self.base_url = base_url.rstrip('/')
        self.client_key = client_key
        self.access_token = access_token
        self.refresh_token = None
        self.session = requests.Session()
        
        # Configuration des en-têtes par défaut
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Optibudget-TestClient/1.0',
        })
        
        # Ajouter la clé client et le token d'accès si fournis
        if self.client_key:
            self.session.headers['X-Client-Key'] = self.client_key
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
        url = f"{self.base_url}/api/accounts/{endpoint.lstrip('/')}"
        
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
            
            # Gérer la réponse
            if response.status_code == 401 and requires_auth:
                print(f"⚠️  Token expiré pour {endpoint}, tentative de rafraîchissement...")
                if self.refresh_token:
                    self._refresh_token()
                    # Réessayer avec le nouveau token
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    if method.upper() == 'GET':
                        response = self.session.get(url, headers=headers)
                    elif method.upper() == 'POST':
                        response = self.session.post(url, json=data, headers=headers)
                    elif method.upper() == 'PUT':
                        response = self.session.put(url, json=data, headers=headers)
                    elif method.upper() == 'DELETE':
                        response = self.session.delete(url, headers=headers)
            
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
    
    def _refresh_token(self) -> bool:
        """Rafraîchit le token d'accès"""
        if not self.refresh_token:
            return False
        
        data = {'refresh': self.refresh_token}
        response = self._make_request('POST', 'token/refresh/', data)
        
        if response['status_code'] == 200:
            self.access_token = response['data'].get('access')
            return True
        return False
    
    def print_response(self, endpoint: str, response: Dict[str, Any]):
        """Affiche une réponse de manière formatée"""
        print(f"{'='*60}")
        print(f"🔗 {endpoint}")
        print(f"📊 Status: {response['status_code']}")
        print(f"🌐 URL: {response['url']}")
        
        if 'error' in response:
            print(f"❌ Erreur: {response['error']}")
        else:
            print(f"📄 Réponse: {json.dumps(response['data'], indent=2, ensure_ascii=False)}")
        print(f"{'='*60}")
    
    # ============================================================================
    # ENDPOINTS D'AUTHENTIFICATION (pas d'authentification requise)
    # ============================================================================
    
    def test_register(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste l'inscription d'un utilisateur"""
        print("🚀 Test d'inscription d'utilisateur...")
        response = self._make_request('POST', 'register/', user_data)
        self.print_response('POST /register/', response)
        return response
    
    def test_login(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Teste la connexion utilisateur"""
        print("🔐 Test de connexion...")
        response = self._make_request('POST', 'login/', credentials)
        
        if response['status_code'] == 200:
            self.access_token = response['data'].get('access')
            self.refresh_token = response['data'].get('refresh')
            print(f"✅ Connexion réussie - Token obtenu")
        
        self.print_response('POST /login/', response)
        return response
    
    def test_token_refresh(self) -> Dict[str, Any]:
        """Teste le rafraîchissement de token"""
        print("🔄 Test de rafraîchissement de token...")
        if not self.refresh_token:
            print("❌ Pas de refresh token disponible")
            return {'status_code': 400, 'error': 'Pas de refresh token'}
        
        data = {'refresh': self.refresh_token}
        response = self._make_request('POST', 'token/refresh/', data)
        
        if response['status_code'] == 200:
            self.access_token = response['data'].get('access')
            print(f"✅ Token rafraîchi avec succès")
        
        self.print_response('POST /token/refresh/', response)
        return response
    
    def test_verify_email(self, token: str) -> Dict[str, Any]:
        """Teste la vérification d'email"""
        print(f"📧 Test de vérification d'email avec token: {token[:20]}...")
        response = self._make_request('GET', f'verify-email/{token}/')
        self.print_response(f'GET /verify-email/{token[:20]}.../', response)
        return response
    
    def test_password_reset_request(self, email: str) -> Dict[str, Any]:
        """Teste la demande de réinitialisation de mot de passe"""
        print(f"🔑 Test de demande de réinitialisation de mot de passe...")
        data = {'email': email}
        response = self._make_request('POST', 'password-reset/', data)
        self.print_response('POST /password-reset/', response)
        return response
    
    def test_password_reset_confirm(self, token: str, new_password: str) -> Dict[str, Any]:
        """Teste la confirmation de réinitialisation de mot de passe"""
        print(f"✅ Test de confirmation de réinitialisation de mot de passe...")
        data = {
            'token': token,
            'new_password': new_password,
            'confirm_password': new_password
        }
        response = self._make_request('POST', f'reset-password/{token}/', data)
        self.print_response(f'POST /reset-password/{token[:20]}.../', response)
        return response
    
    def test_user_choices(self) -> Dict[str, Any]:
        """Teste la récupération des choix utilisateur"""
        print("📋 Test de récupération des choix utilisateur...")
        response = self._make_request('GET', 'choices/')
        self.print_response('GET /choices/', response)
        return response
    
    # ============================================================================
    # ENDPOINTS REQUIÉRANT UNE AUTHENTIFICATION
    # ============================================================================
    
    def test_profile(self) -> Dict[str, Any]:
        """Teste la récupération du profil utilisateur"""
        print("👤 Test de récupération du profil...")
        response = self._make_request('GET', 'profile/', requires_auth=True)
        self.print_response('GET /profile/', response)
        return response
    
    def test_update_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste la mise à jour du profil utilisateur"""
        print("✏️  Test de mise à jour du profil...")
        response = self._make_request('PUT', 'profile/', profile_data, requires_auth=True)
        self.print_response('PUT /profile/', response)
        return response
    
    def test_change_password(self, password_data: Dict[str, str]) -> Dict[str, Any]:
        """Teste le changement de mot de passe"""
        print("🔒 Test de changement de mot de passe...")
        response = self._make_request('POST', 'change-password/', password_data, requires_auth=True)
        self.print_response('POST /change-password/', response)
        return response
    
    def test_preferences(self) -> Dict[str, Any]:
        """Teste la récupération des préférences utilisateur"""
        print("⚙️  Test de récupération des préférences...")
        response = self._make_request('GET', 'preferences/', requires_auth=True)
        self.print_response('GET /preferences/', response)
        return response
    
    def test_update_preferences(self, preferences_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste la mise à jour des préférences utilisateur"""
        print("🔧 Test de mise à jour des préférences...")
        response = self._make_request('PUT', 'preferences/', preferences_data, requires_auth=True)
        self.print_response('PUT /preferences/', response)
        return response
    
    def test_devices_list(self) -> Dict[str, Any]:
        """Teste la liste des appareils"""
        print("📱 Test de liste des appareils...")
        response = self._make_request('GET', 'devices/', requires_auth=True)
        self.print_response('GET /devices/', response)
        return response
    
    def test_device_register(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teste l'enregistrement d'un appareil"""
        print("📱 Test d'enregistrement d'appareil...")
        response = self._make_request('POST', 'devices/register/', device_data, requires_auth=True)
        self.print_response('POST /devices/register/', response)
        return response
    
    def test_device_deactivate(self, device_id: str) -> Dict[str, Any]:
        """Teste la désactivation d'un appareil"""
        print(f"❌ Test de désactivation d'appareil {device_id[:20]}...")
        response = self._make_request('POST', f'devices/{device_id}/deactivate/', requires_auth=True)
        self.print_response(f'POST /devices/{device_id[:20]}.../deactivate/', response)
        return response
    
    def test_device_trust(self, device_id: str) -> Dict[str, Any]:
        """Teste le marquage d'un appareil comme de confiance"""
        print(f"✅ Test de marquage d'appareil comme de confiance {device_id[:20]}...")
        response = self._make_request('POST', f'devices/{device_id}/trust/', requires_auth=True)
        self.print_response(f'POST /devices/{device_id[:20]}.../trust/', response)
        return response
    
    def test_login_attempts(self) -> Dict[str, Any]:
        """Teste la récupération des tentatives de connexion"""
        print("📊 Test de récupération des tentatives de connexion...")
        response = self._make_request('GET', 'login-attempts/', requires_auth=True)
        self.print_response('GET /login-attempts/', response)
        return response
    
    def test_user_stats(self) -> Dict[str, Any]:
        """Teste la récupération des statistiques utilisateur"""
        print("📈 Test de récupération des statistiques utilisateur...")
        response = self._make_request('GET', 'stats/', requires_auth=True)
        self.print_response('GET /stats/', response)
        return response
    
    def test_logout(self) -> Dict[str, Any]:
        """Teste la déconnexion"""
        print("🚪 Test de déconnexion...")
        response = self._make_request('POST', 'logout/', requires_auth=True)
        
        if response['status_code'] == 200:
            self.access_token = None
            self.refresh_token = None
            print("✅ Déconnexion réussie - Tokens supprimés")
        
        self.print_response('POST /logout/', response)
        return response
    
    def test_logout_all_devices(self) -> Dict[str, Any]:
        """Teste la déconnexion de tous les appareils"""
        print("🚪 Test de déconnexion de tous les appareils...")
        response = self._make_request('POST', 'logout-all/', requires_auth=True)
        
        if response['status_code'] == 200:
            self.access_token = None
            self.refresh_token = None
            print("✅ Déconnexion de tous les appareils réussie - Tokens supprimés")
        
        self.print_response('POST /logout-all/', response)
        return response
    
    # ============================================================================
    # ENDPOINTS ADMIN (requièrent des privilèges admin)
    # ============================================================================
    
    def test_admin_users_list(self) -> Dict[str, Any]:
        """Teste la liste des utilisateurs (admin)"""
        print("👥 Test de liste des utilisateurs (admin)...")
        response = self._make_request('GET', 'admin/users/', requires_auth=True)
        self.print_response('GET /admin/users/', response)
        return response
    
    def test_admin_user_detail(self, user_id: int) -> Dict[str, Any]:
        """Teste les détails d'un utilisateur (admin)"""
        print(f"👤 Test de détails utilisateur {user_id} (admin)...")
        response = self._make_request('GET', f'admin/users/{user_id}/', requires_auth=True)
        self.print_response(f'GET /admin/users/{user_id}/', response)
        return response
    
    def test_admin_user_activation(self, user_id: int, activate: bool = True) -> Dict[str, Any]:
        """Teste l'activation/désactivation d'un utilisateur (admin)"""
        action = "activation" if activate else "désactivation"
        print(f"🔧 Test de {action} utilisateur {user_id} (admin)...")
        data = {'is_active': activate}
        response = self._make_request('POST', f'admin/users/{user_id}/activation/', data, requires_auth=True)
        self.print_response(f'POST /admin/users/{user_id}/activation/', response)
        return response
    
    def test_admin_stats(self) -> Dict[str, Any]:
        """Teste les statistiques admin"""
        print("📊 Test de statistiques admin...")
        response = self._make_request('GET', 'admin/stats/', requires_auth=True)
        self.print_response('GET /admin/stats/', response)
        return response
    
    # ============================================================================
    # TESTS COMPLETS
    # ============================================================================
    
    def run_complete_test(self):
        """Exécute une suite complète de tests"""
        print("🚀 Démarrage des tests complets de l'API accounts")
        print("=" * 80)
        
        # Données de test
        test_email = f"test_{int(time.time())}@example.com"
        test_user_data = {
            "username": f"testuser_{int(time.time())}",
            "email": test_email,
            "password": test_password,
            "confirm_password": test_password,
            "first_name": "Test",
            "last_name": "User",
            "compte": "particulier",
            "pays": "Cameroun"
        }
        
        # 1. Tests sans authentification
        print("📋 PHASE 1: Tests sans authentification")
        print("-" * 50)
        
        # Test des choix utilisateur
        self.test_user_choices()
        
        # Test d'inscription
        register_response = self.test_register(test_user_data)
        
        # Test de connexion
        login_response = self.test_login({
            "email": test_email,
            "password": test_password
        })
        
        if login_response['status_code'] != 200:
            print("❌ Échec de la connexion, arrêt des tests")
            return
        
        # 2. Tests avec authentification
        print("🔐 PHASE 2: Tests avec authentification")
        print("-" * 50)
        
        # Test du profil
        self.test_profile()
        
        # Test de mise à jour du profil
        self.test_update_profile({
            "first_name": "Test Updated",
            "last_name": "User Updated"
        })
        
        # Test des préférences
        self.test_preferences()
        
        # Test de mise à jour des préférences
        self.test_update_preferences({
            "theme": "dark",
            "language": "fr",
            "notifications_email": True,
            "notifications_push": False
        })
        
        # Test des appareils
        self.test_devices_list()
        
        # Test d'enregistrement d'appareil
        device_data = {
            "device_name": "Test Device",
            "device_type": "desktop",
            "browser": "Chrome",
            "os": "Windows"
        }
        device_response = self.test_device_register(device_data)
        
        # Test des tentatives de connexion
        self.test_login_attempts()
        
        # Test des statistiques utilisateur
        self.test_user_stats()
        
        # Test de rafraîchissement de token
        self.test_token_refresh()
        
        # 3. Tests admin (si l'utilisateur est admin)
        print("👑 PHASE 3: Tests admin")
        print("-" * 50)
        
        self.test_admin_users_list()
        self.test_admin_stats()
        
        # 4. Tests de déconnexion
        print("🚪 PHASE 4: Tests de déconnexion")
        print("-" * 50)
        
        self.test_logout()
        
    
    def run_security_test(self):
        """Exécute des tests de sécurité"""
        print("🔒 Démarrage des tests de sécurité")
        print("=" * 80)
        
        # Test avec des identifiants incorrects
        print("❌ Test avec identifiants incorrects...")
        self.test_login({
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        
        # Test sans token d'authentification
        print("🚫 Test sans token d'authentification...")
        self.test_profile()
        
        # Test avec un token invalide
        print("🔑 Test avec token invalide...")
        self.access_token = "invalid_token"
        self.test_profile()
        self.access_token = None
        


def main():
    """Fonction principale pour exécuter les tests"""
    print("🧪 Client de test pour l'API accounts Optibudget")
    print("=" * 60)
    
    # Configuration
    base_url = input("🌐 URL de base (défaut: http://localhost:8000): ").strip() or "http://localhost:8000"
    client_key = input("🔑 Clé client (optionnel): ").strip() or None
    
    # Création du client
    client = OptibudgetAccountsClient(base_url, client_key)
    
    print(f"🔧 Configuration:")
    print(f"   URL: {base_url}")
    print(f"   Clé client: {'✅ Fournie' if client_key else '❌ Non fournie'}")
    
    # Menu de choix
    while True:
        print("=" * 50)
        print("📋 MENU DE TESTS")
        print("=" * 50)
        print("1. 🚀 Tests complets")
        print("2. 🔒 Tests de sécurité")
        print("3. 🔐 Test de connexion simple")
        print("4. 👤 Test de profil")
        print("5. 📱 Test des appareils")
        print("6. 👑 Test admin")
        print("7. 🚪 Test de déconnexion")
        print("0. ❌ Quitter")
        
        choice = input("🎯 Votre choix: ").strip()
        
        if choice == "1":
            client.run_complete_test()
        elif choice == "2":
            client.run_security_test()
        elif choice == "3":
            email = input("📧 Email: ").strip()
            password = input("🔑 Mot de passe: ").strip()
            client.test_login({"email": email, "password": password})
        elif choice == "4":
            client.test_profile()
        elif choice == "5":
            client.test_devices_list()
        elif choice == "6":
            client.test_admin_users_list()
            client.test_admin_stats()
        elif choice == "7":
            client.test_logout()
        elif choice == "0":
            break
        else:
            print("❌ Choix invalide")


if __name__ == "__main__":
    main()
