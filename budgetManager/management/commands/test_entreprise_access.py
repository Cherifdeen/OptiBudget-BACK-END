from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Test des restrictions d\'accès aux modèles entreprise'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-users',
            action='store_true',
            help='Créer des utilisateurs de test',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧪 Test des restrictions d\'accès aux modèles entreprise')
        )
        
        if options['create_users']:
            self.create_test_users()
        
        self.run_access_tests()
    
    def create_test_users(self):
        """Créer des utilisateurs de test"""
        self.stdout.write('Création des utilisateurs de test...')
        
        # Créer un utilisateur particulier
        user_particulier, created = User.objects.get_or_create(
            email='particulier@test.com',
            defaults={
                'password': 'testpass123',
                'compte': 'particulier'
            }
        )
        if created:
            user_particulier.set_password('testpass123')
            user_particulier.save()
            self.stdout.write('✅ Utilisateur particulier créé')
        else:
            self.stdout.write('ℹ️  Utilisateur particulier existe déjà')
        
        # Créer un utilisateur entreprise
        user_entreprise, created = User.objects.get_or_create(
            email='entreprise@test.com',
            defaults={
                'password': 'testpass123',
                'compte': 'entreprise'
            }
        )
        if created:
            user_entreprise.set_password('testpass123')
            user_entreprise.save()
            self.stdout.write('✅ Utilisateur entreprise créé')
        else:
            self.stdout.write('ℹ️  Utilisateur entreprise existe déjà')
    
    def run_access_tests(self):
        """Exécuter les tests d'accès"""
        self.stdout.write('\n🔍 Test des restrictions d\'accès...')
        
        # Récupérer les utilisateurs
        try:
            user_particulier = User.objects.get(email='particulier@test.com')
            user_entreprise = User.objects.get(email='entreprise@test.com')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Utilisateurs de test non trouvés. Utilisez --create-users')
            )
            return
        
        # Créer les clients
        client_particulier = Client()
        client_entreprise = Client()
        
        # Authentifier les clients
        self._authenticate_client(client_particulier, user_particulier)
        self._authenticate_client(client_entreprise, user_entreprise)
        
        # Tests des modèles entreprise
        entreprise_models = [
            ('entrees', 'Entrées'),
            ('employes', 'Employés'),
            ('paiements-employes', 'Paiements Employés'),
            ('montants-salaire', 'Montants Salaire'),
        ]
        
        self.stdout.write('\n📋 Tests des modèles réservés aux entreprises :')
        
        for endpoint, name in entreprise_models:
            self.test_entreprise_model_access(
                client_particulier, client_entreprise, endpoint, name
            )
        
        # Tests des modèles accessibles à tous
        all_models = [
            ('budgets', 'Budgets'),
            ('depenses', 'Dépenses'),
            ('categories-depense', 'Catégories Dépense'),
            ('notifications', 'Notifications'),
            ('conseils', 'Conseils'),
        ]
        
        self.stdout.write('\n📋 Tests des modèles accessibles à tous :')
        
        for endpoint, name in all_models:
            self.test_all_users_model_access(
                client_particulier, client_entreprise, endpoint, name
            )
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS('✅ Tests terminés avec succès !')
        )
    
    def _authenticate_client(self, client, user):
        """Authentifier un client"""
        # Se connecter avec le client Django
        client.force_login(user)
    
    def test_entreprise_model_access(self, client_particulier, client_entreprise, endpoint, name):
        """Tester l'accès à un modèle réservé aux entreprises"""
        url = f'/api/budget/{endpoint}/'
        
        # Test avec compte particulier (doit échouer)
        response_particulier = client_particulier.get(url)
        if response_particulier.status_code == status.HTTP_403_FORBIDDEN:
            self.stdout.write(f'✅ {name} : Accès refusé aux particuliers')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ {name} : Accès inattendu pour les particuliers (Status: {response_particulier.status_code})')
            )
        
        # Test avec compte entreprise (doit réussir)
        response_entreprise = client_entreprise.get(url)
        if response_entreprise.status_code == status.HTTP_200_OK:
            self.stdout.write(f'✅ {name} : Accès autorisé aux entreprises')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ {name} : Accès refusé aux entreprises (Status: {response_entreprise.status_code})')
            )
    
    def test_all_users_model_access(self, client_particulier, client_entreprise, endpoint, name):
        """Tester l'accès à un modèle accessible à tous"""
        url = f'/api/budget/{endpoint}/'
        
        # Test avec compte particulier
        response_particulier = client_particulier.get(url)
        if response_particulier.status_code == status.HTTP_200_OK:
            self.stdout.write(f'✅ {name} : Accès autorisé aux particuliers')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ {name} : Accès refusé aux particuliers (Status: {response_particulier.status_code})')
            )
        
        # Test avec compte entreprise
        response_entreprise = client_entreprise.get(url)
        if response_entreprise.status_code == status.HTTP_200_OK:
            self.stdout.write(f'✅ {name} : Accès autorisé aux entreprises')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ {name} : Accès refusé aux entreprises (Status: {response_entreprise.status_code})')
            ) 