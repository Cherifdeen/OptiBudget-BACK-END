# Client de Test pour l'API Accounts SMARTBUDGET

Ce dossier contient un client Python complet pour tester tous les endpoints de l'application `accounts` de SMARTBUDGET.

## 📁 Fichiers

- `test_accounts_client.py` - Client principal pour tester l'API accounts

## 🚀 Utilisation

### Prérequis

```bash
pip install requests
```

### Exécution

```bash
cd testEndpoint
python test_accounts_client.py
```

### Configuration

Le client vous demandera :
1. **URL de base** : L'URL de votre serveur Django (défaut: http://localhost:8000)
2. **Clé client** : La clé client pour l'authentification middleware (optionnel)

## 🔧 Fonctionnalités

### Tests Disponibles

1. **🚀 Tests complets** - Suite complète de tests automatisés
2. **🔒 Tests de sécurité** - Tests de sécurité et d'authentification
3. **🔐 Test de connexion simple** - Test de connexion manuel
4. **👤 Test de profil** - Test des endpoints de profil
5. **📱 Test des appareils** - Test de la gestion des appareils
6. **👑 Test admin** - Test des endpoints administrateur
7. **🚪 Test de déconnexion** - Test de déconnexion

### Endpoints Testés

#### 🔐 Authentification (sans auth requise)
- `POST /register/` - Inscription utilisateur
- `POST /login/` - Connexion utilisateur
- `POST /token/refresh/` - Rafraîchissement de token
- `GET /verify-email/{token}/` - Vérification d'email
- `POST /password-reset/` - Demande de réinitialisation de mot de passe
- `POST /reset-password/{token}/` - Confirmation de réinitialisation
- `GET /choices/` - Choix utilisateur

#### 👤 Profil et Préférences (auth requise)
- `GET /profile/` - Récupération du profil
- `PUT /profile/` - Mise à jour du profil
- `POST /change-password/` - Changement de mot de passe
- `GET /preferences/` - Récupération des préférences
- `PUT /preferences/` - Mise à jour des préférences

#### 📱 Gestion des Appareils (auth requise)
- `GET /devices/` - Liste des appareils
- `POST /devices/register/` - Enregistrement d'appareil
- `POST /devices/{id}/deactivate/` - Désactivation d'appareil
- `POST /devices/{id}/trust/` - Marquage comme de confiance

#### 📊 Statistiques et Sécurité (auth requise)
- `GET /login-attempts/` - Tentatives de connexion
- `GET /stats/` - Statistiques utilisateur
- `POST /logout/` - Déconnexion
- `POST /logout-all/` - Déconnexion de tous les appareils

#### 👑 Administration (auth admin requise)
- `GET /admin/users/` - Liste des utilisateurs
- `GET /admin/users/{id}/` - Détails utilisateur
- `POST /admin/users/{id}/activation/` - Activation/désactivation
- `GET /admin/stats/` - Statistiques admin

## 🔑 En-têtes Requis

Le client gère automatiquement les en-têtes requis par le middleware :

### Authentification JWT
```python
headers['Authorization'] = 'Bearer {access_token}'
```

### Clé Client (si fournie)
```python
headers['X-Client-Key'] = '{client_key}'
```

### En-têtes par défaut
```python
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'User-Agent': 'SMARTBUDGET-TestClient/1.0',
}
```

## 📝 Exemple d'Utilisation

```python
from test_accounts_client import SMARTBUDGETAccountsClient

# Création du client
client = SMARTBUDGETAccountsClient(
    base_url="http://localhost:8000",
    client_key="votre_cle_client"
)

# Test de connexion
response = client.test_login({
    "email": "user@example.com",
    "password": "password123"
})

# Test du profil (après connexion)
if response['status_code'] == 200:
    client.test_profile()
```

## 🔍 Gestion des Erreurs

Le client gère automatiquement :
- **Token expiré** : Rafraîchissement automatique du token
- **Erreurs réseau** : Affichage des erreurs de connexion
- **Réponses d'erreur** : Affichage formaté des erreurs API

## 📊 Affichage des Résultats

Chaque test affiche :
- 🔗 Endpoint testé
- 📊 Code de statut HTTP
- 🌐 URL complète
- 📄 Réponse JSON formatée
- ❌ Erreurs éventuelles

## 🛡️ Tests de Sécurité

Le client inclut des tests de sécurité :
- Tentatives de connexion avec identifiants incorrects
- Accès sans authentification
- Utilisation de tokens invalides
- Tests de permissions

## 🎯 Cas d'Usage

1. **Développement** : Test des nouvelles fonctionnalités
2. **Intégration** : Vérification de l'intégration API
3. **Sécurité** : Tests de sécurité et d'authentification
4. **Documentation** : Exemples d'utilisation des endpoints
5. **Debugging** : Diagnostic des problèmes API

## 📋 Notes Importantes

- Le client simule un navigateur avec `User-Agent: SMARTBUDGET-TestClient/1.0`
- Les tokens JWT sont automatiquement gérés
- Les erreurs sont affichées de manière claire et formatée
- Le client peut être utilisé en mode interactif ou programmatique 