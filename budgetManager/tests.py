from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from .models import (
    Budget, CategorieDepense, Depense, Entree, Employe,
    Notification, Conseil, PaiementEmploye, MontantSalaire
)
from .serializers import (
    BudgetSerializer, CategorieDepenseSerializer, DepenseSerializer
)

User = get_user_model()


class BudgetManagerTestCase(TestCase):
    """Tests de base pour les modèles"""
    
    def setUp(self):
        """Configuration initiale pour tous les tests"""
        self.user_particulier = User.objects.create_user(
            email='particulier@test.com',
            password='testpass123',
            compte='particulier'
        )
        
        self.user_entreprise = User.objects.create_user(
            email='entreprise@test.com',
            password='testpass123',
            compte='entreprise'
        )
        
        self.budget = Budget.objects.create(
            nom='Budget Test',
            montant=1000.0,
            montant_initial=1000.0,
            user=self.user_particulier,
            type_budget='D',
            date_fin=timezone.now().date() + timedelta(days=30)
        )

    def test_budget_creation(self):
        """Test de création d'un budget"""
        self.assertEqual(self.budget.nom, 'Budget Test')
        self.assertEqual(self.budget.montant, 1000.0)
        self.assertEqual(self.budget.user, self.user_particulier)
        self.assertTrue(self.budget.actif)

    def test_categorie_depense_creation(self):
        """Test de création d'une catégorie de dépense"""
        categorie = CategorieDepense.objects.create(
            nom='Alimentation',
            montant=200.0,
            montant_initial=200.0,
            id_budget=self.budget,
            user=self.user_particulier
        )
        
        self.assertEqual(categorie.nom, 'Alimentation')
        self.assertEqual(categorie.montant, 200.0)
        self.assertEqual(categorie.id_budget, self.budget)
        
        # Vérifier que le montant a été déduit du budget
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.montant, 800.0)

    def test_depense_creation(self):
        """Test de création d'une dépense"""
        categorie = CategorieDepense.objects.create(
            nom='Alimentation',
            montant=200.0,
            montant_initial=200.0,
            id_budget=self.budget,
            user=self.user_particulier
        )
        
        depense = Depense.objects.create(
            nom='Courses',
            montant=50.0,
            id_budget=self.budget,
            id_cat_depense=categorie,
            user=self.user_particulier
        )
        
        self.assertEqual(depense.nom, 'Courses')
        self.assertEqual(depense.montant, 50.0)
        self.assertEqual(depense.id_cat_depense, categorie)

    def test_employe_creation(self):
        """Test de création d'un employé (compte entreprise uniquement)"""
        employe = Employe.objects.create(
            nom='Dupont',
            prenom='Jean',
            telephone='0123456789',
            email='jean.dupont@test.com',
            type_employe='EMP',
            poste='Développeur',
            user=self.user_entreprise
        )
        
        self.assertEqual(employe.nom, 'Dupont')
        self.assertEqual(employe.prenom, 'Jean')
        self.assertEqual(employe.type_employe, 'EMP')
        self.assertEqual(employe.actif, 'ES')  # En service par défaut


class BudgetManagerAPITestCase(APITestCase):
    """Tests API pour l'application budgetManager"""
    
    def setUp(self):
        """Configuration initiale pour les tests API"""
        self.user_particulier = User.objects.create_user(
            email='particulier@test.com',
            password='testpass123',
            compte='particulier'
        )
        
        self.user_entreprise = User.objects.create_user(
            email='entreprise@test.com',
            password='testpass123',
            compte='entreprise'
        )
        
        self.client_particulier = APIClient()
        self.client_entreprise = APIClient()
        
        # Authentifier les clients
        self._authenticate_client(self.client_particulier, self.user_particulier)
        self._authenticate_client(self.client_entreprise, self.user_entreprise)

    def _authenticate_client(self, client, user):
        """Authentifier un client API"""
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_budget_list_api(self):
        """Test de l'API de liste des budgets"""
        # Créer un budget
        budget = Budget.objects.create(
            nom='Budget API Test',
            montant=1000.0,
            montant_initial=1000.0,
            user=self.user_particulier
        )
        
        # Tester l'API
        response = self.client_particulier.get('/api/budget/budgets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['nom'], 'Budget API Test')

    def test_budget_creation_api(self):
        """Test de création d'un budget via API"""
        data = {
            'nom': 'Nouveau Budget',
            'montant': 2000.0,
            'date_fin': (timezone.now().date() + timedelta(days=30)).isoformat(),
            'type_budget': 'D'
        }
        
        response = self.client_particulier.post('/api/budget/budgets/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nom'], 'Nouveau Budget')
        self.assertEqual(response.data['montant'], 2000.0)

    def test_entreprise_restrictions(self):
        """Test des restrictions d'accès pour les comptes entreprise"""
        # Test que les comptes particuliers ne peuvent pas accéder aux employés
        response = self.client_particulier.get('/api/budget/employes/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test que les comptes entreprise peuvent accéder aux employés
        response = self.client_entreprise.get('/api/budget/employes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_categorie_depense_api(self):
        """Test de l'API des catégories de dépense"""
        # Créer un budget d'abord
        budget = Budget.objects.create(
            nom='Budget Catégorie Test',
            montant=1000.0,
            montant_initial=1000.0,
            user=self.user_particulier
        )
        
        # Créer une catégorie
        data = {
            'nom': 'Transport',
            'montant': 300.0,
            'id_budget': budget.id
        }
        
        response = self.client_particulier.post('/api/budget/categories-depense/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nom'], 'Transport')
        self.assertEqual(response.data['montant'], 300.0)

    def test_depense_api(self):
        """Test de l'API des dépenses"""
        # Créer un budget et une catégorie
        budget = Budget.objects.create(
            nom='Budget Dépense Test',
            montant=1000.0,
            montant_initial=1000.0,
            user=self.user_particulier
        )
        
        categorie = CategorieDepense.objects.create(
            nom='Alimentation',
            montant=500.0,
            montant_initial=500.0,
            id_budget=budget,
            user=self.user_particulier
        )
        
        # Créer une dépense
        data = {
            'nom': 'Courses alimentaires',
            'montant': 75.0,
            'id_budget': budget.id,
            'id_cat_depense': categorie.id,
            'type_depense': 'DP'
        }
        
        response = self.client_particulier.post('/api/budget/depenses/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nom'], 'Courses alimentaires')
        self.assertEqual(response.data['montant'], 75.0)


class SerializerTestCase(TestCase):
    """Tests pour les sérialiseurs"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123',
            compte='particulier'
        )
        
        self.budget = Budget.objects.create(
            nom='Budget Serializer Test',
            montant=1000.0,
            montant_initial=1000.0,
            user=self.user
        )

    def test_budget_serializer_validation(self):
        """Test de validation du sérialiseur Budget"""
        # Test validation nom unique
        data = {
            'nom': 'Budget Serializer Test',  # Nom déjà existant
            'montant': 2000.0
        }
        
        serializer = BudgetSerializer(data=data, context={'request': type('obj', (object,), {'user': self.user})})
        self.assertFalse(serializer.is_valid())
        self.assertIn('nom', serializer.errors)

    def test_categorie_serializer_validation(self):
        """Test de validation du sérialiseur CategorieDepense"""
        # Test validation montant positif
        data = {
            'nom': 'Catégorie Test',
            'montant': -100.0,  # Montant négatif
            'id_budget': self.budget.id
        }
        
        serializer = CategorieDepenseSerializer(data=data, context={'request': type('obj', (object,), {'user': self.user})})
        self.assertFalse(serializer.is_valid())
        self.assertIn('montant', serializer.errors)

    def test_depense_serializer_validation(self):
        """Test de validation du sérialiseur Depense"""
        # Test validation montant positif
        data = {
            'nom': 'Dépense Test',
            'montant': -50.0,  # Montant négatif
            'id_budget': self.budget.id
        }
        
        serializer = DepenseSerializer(data=data, context={'request': type('obj', (object,), {'user': self.user})})
        self.assertFalse(serializer.is_valid())
        self.assertIn('montant', serializer.errors)


class NotificationTestCase(TestCase):
    """Tests pour le système de notifications"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123',
            compte='particulier'
        )

    def test_notification_creation(self):
        """Test de création de notification"""
        notification = Notification.objects.create(
            message='Test notification',
            type_notification='INFO',
            user=self.user
        )
        
        self.assertEqual(notification.message, 'Test notification')
        self.assertEqual(notification.type_notification, 'INFO')
        self.assertFalse(notification.viewed)

    def test_notification_mark_as_read(self):
        """Test de marquage d'une notification comme lue"""
        notification = Notification.objects.create(
            message='Test notification',
            type_notification='INFO',
            user=self.user
        )
        
        notification.viewed = True
        notification.save()
        
        self.assertTrue(notification.viewed)


class EmployeTestCase(TestCase):
    """Tests spécifiques pour les employés (compte entreprise)"""
    
    def setUp(self):
        self.user_entreprise = User.objects.create_user(
            email='entreprise@test.com',
            password='testpass123',
            compte='entreprise'
        )

    def test_employe_status_changes(self):
        """Test des changements de statut d'employé"""
        employe = Employe.objects.create(
            nom='Test',
            prenom='Employé',
            telephone='0123456789',
            email='test@employe.com',
            type_employe='EMP',
            poste='Testeur',
            user=self.user_entreprise
        )
        
        # Test changement de statut
        employe.actif = 'EC'  # En congé
        employe.save()
        
        self.assertEqual(employe.actif, 'EC')

    def test_employe_type_choices(self):
        """Test des choix de type d'employé"""
        employe = Employe.objects.create(
            nom='Test',
            prenom='Employé',
            telephone='0123456789',
            email='test@employe.com',
            type_employe='DIR',  # Direction
            poste='Directeur',
            user=self.user_entreprise
        )
        
        self.assertEqual(employe.type_employe, 'DIR')
        self.assertEqual(employe.get_type_employe_display(), 'Direction')


class PaiementEmployeTestCase(TestCase):
    """Tests pour les paiements d'employés"""
    
    def setUp(self):
        self.user_entreprise = User.objects.create_user(
            email='entreprise@test.com',
            password='testpass123',
            compte='entreprise'
        )
        
        self.budget = Budget.objects.create(
            nom='Budget Salaires',
            montant=10000.0,
            montant_initial=10000.0,
            user=self.user_entreprise
        )
        
        self.employe = Employe.objects.create(
            nom='Test',
            prenom='Employé',
            telephone='0123456789',
            email='test@employe.com',
            type_employe='EMP',
            poste='Développeur',
            user=self.user_entreprise
        )

    def test_paiement_employe_creation(self):
        """Test de création d'un paiement d'employé"""
        paiement = PaiementEmploye.objects.create(
            id_employe=self.employe,
            montant=2500.0,
            type_paiement='SALAIRE',
            id_budget=self.budget,
            user=self.user_entreprise
        )
        
        self.assertEqual(paiement.id_employe, self.employe)
        self.assertEqual(paiement.montant, 2500.0)
        self.assertEqual(paiement.type_paiement, 'SALAIRE')
        self.assertEqual(paiement.id_budget, self.budget)


class MontantSalaireTestCase(TestCase):
    """Tests pour les montants de salaire"""
    
    def setUp(self):
        self.user_entreprise = User.objects.create_user(
            email='entreprise@test.com',
            password='testpass123',
            compte='entreprise'
        )

    def test_montant_salaire_creation(self):
        """Test de création d'un montant de salaire"""
        montant_salaire = MontantSalaire.objects.create(
            user=self.user_entreprise,
            salaire_direction=5000.0,
            bonus_direction=500.0,
            salaire_cadre=3500.0,
            bonus_cadre=300.0,
            salaire_employe=2500.0,
            bonus_employe=200.0
        )
        
        self.assertEqual(montant_salaire.salaire_direction, 5000.0)
        self.assertEqual(montant_salaire.bonus_direction, 500.0)
        self.assertEqual(montant_salaire.salaire_cadre, 3500.0)
        self.assertEqual(montant_salaire.salaire_employe, 2500.0)
