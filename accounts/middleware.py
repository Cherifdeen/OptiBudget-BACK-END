from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.utils import timezone
from user_agents import parse
import uuid

class DeviceDetectionMiddleware(MiddlewareMixin):
    """Middleware pour détecter automatiquement les appareils"""
    
    def process_request(self, request):
        # Détecter l'appareil seulement pour les utilisateurs authentifiés
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_agent_string = request.META.get('HTTP_USER_AGENT', '')
            user_agent = parse(user_agent_string)
            
            # Extraire les informations de l'appareil
            device_info = {
                'device_name': self.get_device_name(user_agent),
                'device_type': self.get_device_type(user_agent),
                'browser': user_agent.browser.family,
                'os': user_agent.os.family,
                'user_agent': user_agent_string,
            }
            
            # Stocker les informations dans la requête pour utilisation ultérieure
            request.device_info = device_info
    
    def get_device_name(self, user_agent):
        """Génère un nom d'appareil basé sur les informations du user agent"""
        if user_agent.is_mobile:
            return f"{user_agent.device.family} Mobile"
        elif user_agent.is_tablet:
            return f"{user_agent.device.family} Tablet"
        elif user_agent.is_pc:
            return f"{user_agent.os.family} Desktop"
        else:
            return "Appareil inconnu"
    
    def get_device_type(self, user_agent):
        """Détermine le type d'appareil"""
        if user_agent.is_mobile:
            return "mobile"
        elif user_agent.is_tablet:
            return "tablet"
        elif user_agent.is_pc:
            return "desktop"
        else:
            return "unknown"

class SecurityMiddleware(MiddlewareMixin):
    """Middleware pour la sécurité et la gestion des tentatives de connexion"""
    
    def process_request(self, request):
        # Vérifier les tentatives de connexion échouées par IP
        if request.path.endswith('/login/') and request.method == 'POST':
            ip_address = self.get_client_ip(request)
            
            # Ici vous pourriez implémenter une logique pour limiter les tentatives par IP
            # Pour l'instant, nous laissons la logique dans les vues
            pass
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP réelle du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ActivityTrackingMiddleware(MiddlewareMixin):
    """Middleware pour suivre l'activité des utilisateurs"""
    
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Mettre à jour la dernière activité
            request.user.last_activity = timezone.now()
            request.user.save(update_fields=['last_activity']) 