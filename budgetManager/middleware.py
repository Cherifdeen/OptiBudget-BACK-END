from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status
import re


class EntrepriseAccessMiddleware(MiddlewareMixin):
    """
    Middleware pour vérifier l'accès aux endpoints réservés aux comptes entreprise
    """
    
    # Patterns d'URLs réservés aux comptes entreprise
    ENTREPRISE_ONLY_PATTERNS = [
        r'^/api/budget/entrees/',
        r'^/api/budget/employes/',
        r'^/api/budget/paiements-employes/',
        r'^/api/budget/montants-salaire/',
    ]
    
    def process_request(self, request):
        """
        Vérifie les permissions avant de traiter la requête
        """
        # Vérifier si l'utilisateur est authentifié
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        # Vérifier si l'URL correspond à un pattern réservé aux entreprises
        path = request.path_info
        is_entreprise_endpoint = any(
            re.match(pattern, path) for pattern in self.ENTREPRISE_ONLY_PATTERNS
        )
        
        if is_entreprise_endpoint:
            # Vérifier le type de compte
            if not hasattr(request.user, 'compte'):
                return JsonResponse({
                    'error': 'Type de compte non défini',
                    'detail': 'Votre compte ne possède pas de type défini. Contactez l\'administrateur.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if request.user.compte != 'entreprise':
                return JsonResponse({
                    'error': 'Accès réservé aux comptes entreprise',
                    'detail': 'Cette fonctionnalité n\'est disponible que pour les comptes de type entreprise. '
                              'Les modèles Entree, Employe, PaiementEmploye et MontantSalaire sont réservés aux entreprises.',
                    'required_account_type': 'entreprise',
                    'current_account_type': request.user.compte
                }, status=status.HTTP_403_FORBIDDEN)
        
        return None 