from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class EntreprisePermission(permissions.BasePermission):
    """
    Permission personnalisée pour vérifier que l'utilisateur a un compte de type 'entreprise'
    """
    
    def has_permission(self, request, view):
        """
        Vérifie si l'utilisateur a un compte entreprise
        """
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'compte'):
            return False
        
        if request.user.compte != 'entreprise':
            raise PermissionDenied(
                "Accès réservé aux comptes de type entreprise. "
                "Cette fonctionnalité n'est disponible que pour les comptes entreprise."
            )
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Vérifie les permissions au niveau de l'objet
        """
        # Vérifier d'abord les permissions de base
        if not self.has_permission(request, view):
            return False
        
        # Vérifier que l'objet appartient à l'utilisateur
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return True


class EntrepriseOrReadOnlyPermission(permissions.BasePermission):
    """
    Permission qui permet la lecture à tous les utilisateurs authentifiés
    mais limite l'écriture aux comptes entreprise
    """
    
    def has_permission(self, request, view):
        """
        Vérifie les permissions selon la méthode HTTP
        """
        if not request.user.is_authenticated:
            return False
        
        # Permettre la lecture (GET, HEAD, OPTIONS) à tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Pour les méthodes d'écriture, vérifier le type de compte
        if not hasattr(request.user, 'compte'):
            return False
        
        if request.user.compte != 'entreprise':
            raise PermissionDenied(
                "Modification réservée aux comptes de type entreprise. "
                "Cette fonctionnalité n'est disponible que pour les comptes entreprise."
            )
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Vérifie les permissions au niveau de l'objet
        """
        # Permettre la lecture à tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, 'user'):
                return obj.user == request.user
            return True
        
        # Pour les méthodes d'écriture, vérifier le type de compte et la propriété
        if not hasattr(request.user, 'compte'):
            return False
        
        if request.user.compte != 'entreprise':
            return False
        
        # Vérifier que l'objet appartient à l'utilisateur
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return True 