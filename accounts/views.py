from django.contrib.auth import login, logout
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate
from tasks.sendMail import send_email_task
from Optibudget.settings import DEFAULT_FROM_EMAIL



from .models import CustomUser, UserPreferences
from .serializers import (
    CustomUserSerializer, UserRegistrationSerializer, UserLoginSerializer,
    UserProfileSerializer, UserUpdateSerializer, PasswordChangeSerializer,
    UserListSerializer, UserPreferencesSerializer, UserPreferencesUpdateSerializer,
    UserChoicesSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    """Pagination personnalisée"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserRegistrationView(APIView):
    """
    Vue pour l'inscription des utilisateurs
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Création du token d'authentification
            token, created = Token.objects.get_or_create(user=user)
            
            # Données de réponse
            response_data = {
                'message': 'Inscription réussie',
                'user': UserProfileSerializer(user).data,
                'token': token.key
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """
    Vue pour la connexion des utilisateurs
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Connexion de l'utilisateur
            login(request, user)
            
            # Récupération ou création du token
            token, created = Token.objects.get_or_create(user=user)
            
            response_data = {
                'message': 'Connexion réussie',
                'user': UserProfileSerializer(user).data,
                'token': token.key
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    """
    Vue pour la déconnexion des utilisateurs
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Suppression du token
            request.user.auth_token.delete()
        except:
            pass
        
        # Déconnexion
        logout(request)
        
        return Response(
            {'message': 'Déconnexion réussie'}, 
            status=status.HTTP_200_OK
        )


class UserProfileView(APIView):
    """
    Vue pour récupérer et mettre à jour le profil utilisateur
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer le profil de l'utilisateur connecté"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Mettre à jour le profil utilisateur"""
        serializer = UserUpdateSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profil mis à jour avec succès',
                'user': UserProfileSerializer(request.user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    """
    Vue pour changer le mot de passe
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Mot de passe changé avec succès'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordVerificationView(APIView):
    """
    Vue pour vérifier si le mot de passe saisi par l'utilisateur est correct
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Vérifier le mot de passe de l'utilisateur connecté
        """
        password = request.data.get('password')
        
        if not password:
            return Response(
                {'error': 'Le mot de passe est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérification du mot de passe avec authenticate
        user = authenticate(
            username=request.user.username, 
            password=password
        )
        
        if user is not None:
            return Response({
                'valid': True,
                'message': 'Mot de passe correct'
            })
        else:
            return Response({
                'valid': False,
                'message': 'Mot de passe incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        

class UserPreferencesView(APIView):
    """
    Vue pour gérer les préférences utilisateur
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Récupérer les préférences utilisateur"""
        preferences, created = UserPreferences.objects.get_or_create(
            user=request.user
        )
        serializer = UserPreferencesSerializer(preferences)
        return Response(serializer.data)
    
    def put(self, request):
        """Mettre à jour les préférences utilisateur"""
        preferences, created = UserPreferences.objects.get_or_create(
            user=request.user
        )
        serializer = UserPreferencesUpdateSerializer(
            preferences, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Préférences mises à jour avec succès',
                'preferences': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    """
    Vue pour lister les utilisateurs (admin seulement)
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Filtres
    filterset_fields = ['compte', 'pays', 'statut_compte', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'username', 'email']
    ordering = ['-date_joined']


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vue pour récupérer, mettre à jour ou supprimer un utilisateur spécifique (admin)
    """
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.IsAdminUser]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserProfileSerializer
        return UserUpdateSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Désactiver l'utilisateur au lieu de le supprimer"""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({
            'message': 'Utilisateur désactivé avec succès'
        })


class UserActivationView(APIView):
    """
    Vue pour activer/désactiver un utilisateur (admin)
    """
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        action = request.data.get('action')  # 'activate' ou 'deactivate'
        
        if action == 'activate':
            user.is_active = True
            user.statut_compte = True
            message = 'Utilisateur activé avec succès'
        elif action == 'deactivate':
            user.is_active = False
            user.statut_compte = False
            message = 'Utilisateur désactivé avec succès'
        else:
            return Response(
                {'error': 'Action non valide'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.save()
        return Response({
            'message': message,
            'user': UserListSerializer(user).data
        })


class UserStatsView(APIView):
    """
    Vue pour les statistiques des utilisateurs (admin)
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        stats = {
            'total_users': CustomUser.objects.count(),
            'active_users': CustomUser.objects.filter(is_active=True).count(),
            'inactive_users': CustomUser.objects.filter(is_active=False).count(),
            'enterprise_accounts': CustomUser.objects.filter(compte='entreprise').count(),
            'individual_accounts': CustomUser.objects.filter(compte='particulier').count(),
            'users_by_country': dict(
                CustomUser.objects.values_list('pays')
                .annotate(count=models.Count('pays'))
                .order_by('-count')
            )
        }
        return Response(stats)


class UserChoicesView(APIView):
    """
    Vue pour récupérer les choix disponibles pour les formulaires
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        serializer = UserChoicesSerializer()
        return Response(serializer.to_representation(None))


# Vues basées sur les fonctions pour des cas spécifiques

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_username_availability(request):
    """
    Vérifier la disponibilité d'un nom d'utilisateur
    """
    username = request.data.get('username')
    if not username:
        return Response(
            {'error': 'Le nom d\'utilisateur est requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    is_available = not CustomUser.objects.filter(username=username).exists()
    return Response({
        'username': username,
        'available': is_available
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_email_availability(request):
    """
    Vérifier la disponibilité d'un email
    """
    email = request.data.get('email')
    if not email:
        return Response(
            {'error': 'L\'email est requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    is_available = not CustomUser.objects.filter(email=email).exists()
    return Response({
        'email': email,
        'available': is_available
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_profile_image(request):
    """
    Upload d'image de profil
    """
    if 'image' not in request.FILES:
        return Response(
            {'error': 'Aucune image fournie'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    user.img_profil = request.FILES['image']
    user.save()
    
    return Response({
        'message': 'Image de profil mise à jour avec succès',
        'image_url': user.img_profil.url if user.img_profil else None
    })


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_profile_image(request):
    """
    Supprimer l'image de profil
    """
    user = request.user
    if user.img_profil:
        user.img_profil.delete()
        user.img_profil = None
        user.save()
    
    return Response({
        'message': 'Image de profil supprimée avec succès'
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    """
    Demande de réinitialisation de mot de passe
    """
    email = request.data.get('email')
    if not email:
        return Response(
            {'error': 'L\'email est requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = CustomUser.objects.get(email=email)
        
        # Génération du token de réinitialisation
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Envoi de l'email (à adapter selon votre configuration)
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"



        """

        Redis celery

        """


        send_email_task.delay(
            subject='Réinitialisation de mot de passe',
            message=f'Cliquez sur le lien suivant pour réinitialiser votre mot de passe : {reset_url}',
            from_email=DEFAULT_FROM_EMAIL,
            recipient_list=[email]
        )
        
        return Response({
            'message': 'Un email de réinitialisation a été envoyé'
        })
    
    except CustomUser.DoesNotExist:
        # Pour des raisons de sécurité, on ne révèle pas si l'email existe
        return Response({
            'message': 'Si cet email existe, un lien de réinitialisation a été envoyé'
        })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request, uidb64, token):
    """
    Confirmation de réinitialisation de mot de passe
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    
    if user and default_token_generator.check_token(user, token):
        new_password = request.data.get('new_password')
        if not new_password:
            return Response(
                {'error': 'Le nouveau mot de passe est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation du mot de passe
        try:
            from django.contrib.auth.password_validation import validate_password
            validate_password(new_password)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        send_email_task.delay(
            subject='Mot de passe réinitialisé',
            message='Votre mot de passe a été réinitialisé avec succès.',
            from_email=DEFAULT_FROM_EMAIL,
            recipient_list=[user.email]
        )
        return Response({
            'message': 'Mot de passe réinitialisé avec succès'
        })
    
    return Response(
        {'error': 'Lien de réinitialisation invalide'}, 
        status=status.HTTP_400_BAD_REQUEST
    )