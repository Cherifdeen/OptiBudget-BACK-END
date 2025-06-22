"""
Configuration personnalisée pour drf-yasg
"""
from drf_yasg import openapi

# Configuration de sécurité JWT
JWT_SECURITY = [
    {
        'Bearer': []
    }
]

# Paramètres de sécurité
JWT_SECURITY_DEFINITION = {
    'Bearer': {
        'type': 'apiKey',
        'name': 'Authorization',
        'in': 'header',
        'description': 'Token JWT au format: Bearer <token>'
    }
}

# Paramètres de sécurité
security_definitions = {
    'Bearer': {
        'type': 'apiKey',
        'name': 'Authorization',
        'in': 'header',
        'description': 'Token JWT au format: Bearer <token>'
    }
}

# Tags pour organiser les endpoints
tags = [
    {
        'name': 'Authentification',
        'description': 'Endpoints pour l\'authentification et la gestion des comptes utilisateurs'
    },
    {
        'name': 'Profil Utilisateur',
        'description': 'Gestion du profil utilisateur et des préférences'
    },
    {
        'name': 'Budgets',
        'description': 'Gestion des budgets et de leurs catégories'
    },
    {
        'name': 'Dépenses',
        'description': 'Gestion des dépenses et des catégories de dépenses'
    },
    {
        'name': 'Entrées',
        'description': 'Gestion des entrées financières (comptes entreprise)'
    },
    {
        'name': 'Employés',
        'description': 'Gestion des employés et des paiements (comptes entreprise)'
    },
    {
        'name': 'Notifications',
        'description': 'Gestion des notifications utilisateur'
    },
    {
        'name': 'Conseils IA',
        'description': 'Conseils intelligents générés par l\'IA'
    },
    {
        'name': 'Rapports',
        'description': 'Génération de rapports et statistiques'
    }
]

# Réponses communes
common_responses = {
    '401': openapi.Response(
        description='Non authentifié',
        examples={
            'application/json': {
                'detail': 'Les informations d\'authentification n\'ont pas été fournies.'
            }
        }
    ),
    '401_client_key': openapi.Response(
        description='Clé client manquante',
        examples={
            'application/json': {
                'detail': 'Clé client manquante.'
            }
        }
    ),
    '403': openapi.Response(
        description='Accès interdit',
        examples={
            'application/json': {
                'detail': 'Vous n\'avez pas la permission d\'effectuer cette action.'
            }
        }
    ),
    '403_client_key': openapi.Response(
        description='Clé client invalide ou inactive',
        examples={
            'application/json': {
                'detail': 'Clé client invalide ou inactive.'
            }
        }
    ),
    '404': openapi.Response(
        description='Ressource non trouvée',
        examples={
            'application/json': {
                'detail': 'La ressource demandée n\'existe pas.'
            }
        }
    ),
    '500': openapi.Response(
        description='Erreur serveur interne',
        examples={
            'application/json': {
                'detail': 'Une erreur interne s\'est produite.'
            }
        }
    )
}

# Paramètres de requête communs
common_parameters = {
    'page': openapi.Parameter(
        'page',
        openapi.IN_QUERY,
        description="Numéro de page pour la pagination",
        type=openapi.TYPE_INTEGER,
        default=1
    ),
    'page_size': openapi.Parameter(
        'page_size',
        openapi.IN_QUERY,
        description="Nombre d'éléments par page",
        type=openapi.TYPE_INTEGER,
        default=20
    ),
    'ordering': openapi.Parameter(
        'ordering',
        openapi.IN_QUERY,
        description="Champ de tri (préfixer avec '-' pour tri décroissant)",
        type=openapi.TYPE_STRING
    ),
    'search': openapi.Parameter(
        'search',
        openapi.IN_QUERY,
        description="Terme de recherche",
        type=openapi.TYPE_STRING
    )
} 