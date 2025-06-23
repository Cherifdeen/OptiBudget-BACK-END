#!/usr/bin/env python3
"""
Script de test pour vérifier les templates de réinitialisation de mot de passe
"""

import requests
import sys

BASE_URL = "http://127.0.0.1:8001"

def test_template_urls():
    """Teste l'accessibilité des templates de réinitialisation de mot de passe"""
    
    urls_to_test = [
        "/password-reset/",
        "/password-reset/done/",
        "/reset-password/complete/",
        "/email-verified/",
    ]
    
    print("🧪 Test des templates de réinitialisation de mot de passe")
    print("=" * 60)
    
    for url in urls_to_test:
        full_url = BASE_URL + url
        try:
            response = requests.get(full_url, timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {url} - Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   📄 Template accessible")
            else:
                print(f"   ❌ Erreur: {response.text[:100]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {url} - Erreur de connexion: {e}")
        
        print()

def test_api_endpoints():
    """Teste les endpoints API pour comparaison"""
    
    print("🔌 Test des endpoints API")
    print("=" * 60)
    
    api_urls = [
        "/api/accounts/login/",
        "/api/accounts/register/",
    ]
    
    for url in api_urls:
        full_url = BASE_URL + url
        try:
            response = requests.get(full_url, timeout=5)
            status = "✅" if response.status_code in [200, 405] else "❌"
            print(f"{status} {url} - Status: {response.status_code}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ {url} - Erreur de connexion: {e}")
        
        print()

if __name__ == "__main__":
    print("🚀 Test des URLs de réinitialisation de mot de passe")
    print(f"📍 Serveur: {BASE_URL}")
    print()
    
    test_template_urls()
    test_api_endpoints()
    
    print("✅ Tests terminés !")
    print("\n📝 Instructions pour le frontend :")
    print("- Utilisez /password-reset/ pour la demande de réinitialisation")
    print("- Utilisez /reset-password/<token>/ pour confirmer la réinitialisation")
    print("- Les emails pointeront vers ces nouvelles URLs") 