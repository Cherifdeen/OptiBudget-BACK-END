from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import CustomUser, UserPreferences, UserDevice, LoginAttempt
import uuid

class UserPreferencesSerializer(serializers.ModelSerializer):
    """
    Serializer pour les préférences utilisateur
    """
    class Meta:
        model = UserPreferences
        fields = ['notifications_email', 'notifications_push', 'two_factor_auth', 'theme']


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer principal pour le modèle CustomUser
    """
    preferences = UserPreferencesSerializer(read_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'nom_entr', 'date_naiss', 'img_profil', 'compte', 
            'profession', 'pays', 'devise', 'langue', 'statut_compte',
            'password', 'password_confirm', 'preferences', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }
    
    def get_full_name(self, obj):
        """Retourne le nom complet de l'utilisateur"""
        return obj.get_full_name()
    
    def validate_email(self, value):
        """Validation de l'email pour éviter les doublons"""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value
    
    def validate_username(self, value):
        """Validation du nom d'utilisateur"""
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value
    
    def validate(self, attrs):
        """Validation globale du serializer"""
        # Vérification des mots de passe
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        
        # Validation du mot de passe Django
        password = attrs.get('password')
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                raise serializers.ValidationError({'password': list(e.messages)})
        
        # Validation pour les comptes entreprise
        if attrs.get('compte') == 'entreprise' and not attrs.get('nom_entr'):
            raise serializers.ValidationError({
                'nom_entr': "Le nom de l'entreprise est requis pour les comptes entreprise."
            })
        
        return attrs
    
    def create(self, validated_data):
        """Création d'un nouvel utilisateur"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Création automatique des préférences utilisateur
        UserPreferences.objects.create(user=user)
        
        return user
    
    def update(self, instance, validated_data):
        """Mise à jour d'un utilisateur existant"""
        password = validated_data.pop('password', None)
        validated_data.pop('password_confirm', None)
        
        # Mise à jour des champs
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Mise à jour du mot de passe si fourni
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Sérialiseur personnalisé pour l'obtention de tokens JWT"""
    
    def validate(self, attrs):
        # Récupérer l'email et le mot de passe
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Vérifier si l'utilisateur existe
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError('Email ou mot de passe incorrect.')
            
            # Vérifier si le compte est verrouillé
            if user.is_account_locked():
                raise serializers.ValidationError('Votre compte est temporairement verrouillé. Réessayez plus tard.')
            
            # Authentifier l'utilisateur
            user = authenticate(email=email, password=password)
            
            if not user:
                # Incrémenter les tentatives échouées
                try:
                    user = CustomUser.objects.get(email=email)
                    user.increment_failed_attempts()
                    
                    # Enregistrer la tentative échouée
                    LoginAttempt.objects.create(
                        user=user,
                        ip_address=self.context['request'].META.get('REMOTE_ADDR'),
                        user_agent=self.context['request'].META.get('HTTP_USER_AGENT', ''),
                        success=False
                    )
                except CustomUser.DoesNotExist:
                    pass
                
                raise serializers.ValidationError('Email ou mot de passe incorrect.')
            
            # Réinitialiser les tentatives échouées en cas de succès
            user.failed_login_attempts = 0
            user.last_login_ip = self.context['request'].META.get('REMOTE_ADDR')
            user.last_activity = timezone.now()
            user.save()
            
            # Enregistrer la tentative réussie
            LoginAttempt.objects.create(
                user=user,
                ip_address=self.context['request'].META.get('REMOTE_ADDR'),
                user_agent=self.context['request'].META.get('HTTP_USER_AGENT', ''),
                success=True
            )
            
            # Générer les tokens
            refresh = self.get_token(user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_email_verified': user.is_email_verified,
                }
            }
            
            return data
        else:
            raise serializers.ValidationError('Email et mot de passe requis.')


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Sérialiseur pour l'inscription d'un nouvel utilisateur"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm', 
                 'phone', 'nom_entr', 'date_naiss', 'compte', 'profession', 'pays', 'devise', 'langue']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(**validated_data)
        
        # Créer les préférences par défaut
        UserPreferences.objects.create(user=user)
        
        return user


class UserDeviceSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la gestion des appareils"""
    
    class Meta:
        model = UserDevice
        fields = ['device_id', 'device_name', 'device_type', 'browser', 'os', 
                 'ip_address', 'is_active', 'is_trusted', 'last_used', 'created_at']
        read_only_fields = ['device_id', 'ip_address', 'last_used', 'created_at']


class DeviceRegistrationSerializer(serializers.ModelSerializer):
    """Sérialiseur pour l'enregistrement d'un nouvel appareil"""
    
    class Meta:
        model = UserDevice
        fields = ['device_name', 'device_type', 'browser', 'os', 'user_agent']
    
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        
        # Créer l'appareil
        device = UserDevice.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            **validated_data
        )
        
        return device


class UserProfileSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le profil utilisateur"""
    devices = UserDeviceSerializer(many=True, read_only=True)
    preferences = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'nom_entr', 
                 'date_naiss', 'img_profil', 'compte', 'profession', 'pays', 'devise', 
                 'langue', 'statut_compte', 'is_email_verified', 'date_joined', 
                 'last_activity', 'devices', 'preferences']
        read_only_fields = ['id', 'email', 'is_email_verified', 'date_joined', 'last_activity']
    
    def get_preferences(self, obj):
        try:
            prefs = obj.preferences
            return {
                'notifications_email': prefs.notifications_email,
                'notifications_push': prefs.notifications_push,
                'two_factor_auth': prefs.two_factor_auth,
                'theme': prefs.theme,
            }
        except UserPreferences.DoesNotExist:
            return None


class ChangePasswordSerializer(serializers.Serializer):
    """Sérialiseur pour le changement de mot de passe"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Les nouveaux mots de passe ne correspondent pas.")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("L'ancien mot de passe est incorrect.")
        return value
    

class EmailVerificationSerializer(serializers.Serializer):
    """Sérialiseur pour la vérification d'email"""
    token = serializers.UUIDField()


class PasswordResetRequestSerializer(serializers.Serializer):
    """Sérialiseur pour la demande de réinitialisation de mot de passe"""
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Sérialiseur pour la confirmation de réinitialisation de mot de passe"""
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des utilisateurs (admin)
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'full_name', 'compte', 
            'pays', 'statut_compte', 'is_active', 'date_joined'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserPreferencesUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour mettre à jour les préférences utilisateur
    """
    class Meta:
        model = UserPreferences
        fields = ['notifications_email', 'notifications_push', 'two_factor_auth', 'theme']


# Serializer pour les choix des champs (utile pour les formulaires dynamiques)
class UserChoicesSerializer(serializers.Serializer):
    """
    Serializer pour récupérer les choix disponibles pour les champs
    """
    def to_representation(self, instance):
        return {
            'compte_choices': dict(CustomUser.TYPE_COMPTE),
            'pays_choices': dict(CustomUser.PAYS),
            'devise_choices': dict(CustomUser.DEVISES),
            'langue_choices': dict(CustomUser.LANGUES),
            'theme_choices': dict(UserPreferences.THEMES) if hasattr(UserPreferences, 'THEMES') else {}
        }


class LoginAttemptSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les tentatives de connexion"""
    
    class Meta:
        model = LoginAttempt
        fields = ['ip_address', 'user_agent', 'success', 'timestamp', 'device']
        read_only_fields = ['ip_address', 'user_agent', 'success', 'timestamp', 'device']