
import requests

# Configuration
endpoint = "http://127.0.0.1:8000/api/accounts/auth/login/"

headers = {
    'X-Client-Key': "7c9195231bf247ff851e13bd5f540583h",
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'User-Agent': 'DRFLoginClient/1.0 Python'
}

data = {
    "username": "admin1",
    "password": "1234"
}

# Requête POST avec tous les paramètres
response = requests.post(
    endpoint,
    json=data,      # Utilise json= pour encoder automatiquement
    headers=headers
)

print(f"Status Code: {response.status_code}")

# Affichage de la réponse
if response.status_code == 200:
    print("Connexion réussie !")
    try:
        result = response.json()
        print(f"Réponse: {result}")
        
        # Récupération du token
        if 'token' in result:
            print(f"Token DRF: {result['token']}")
        elif 'access' in result:
            print(f"Token JWT: {result['access']}")
    except ValueError:
        print("Réponse non-JSON:", response.text)
else:
    print(f"Erreur de connexion: {response.status_code}")
    print(f"Réponse: {response.text}")