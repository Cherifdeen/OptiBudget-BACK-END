from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import (
    Budget, CategorieDepense, Depense, Entree, Employe, 
    Notification, Conseil, PaiementEmploye, MontantSalaire
)
from rest_framework.decorators import action


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id','nom', 'montant','montant_initial', 'date_fin', 'description', 'type_budget','user']
        read_only_fields = ('user', 'created_at', 'updated_at')

    def validate_nom(self, value):
        """Vérifier que le nom du budget n'existe pas déjà pour cet utilisateur"""
        user = self.context['request'].user
        
        # Pour la mise à jour, exclure l'instance actuelle
        queryset = Budget.objects.filter(user=user, nom=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                "Un budget avec ce nom existe déjà."
            )
        return value
    

    def validate_date_fin(self, value):
        """Vérifier que la date limite soit supérieure à 3 jours"""
        if value:
            min_date = timezone.now().date() + timedelta(days=3)
            if value <= min_date:
                raise serializers.ValidationError(
                    "La date limite doit être supérieure à 3 jours à partir d'aujourd'hui."
                )
        return value

    def validate_montant(self, value):
        """Vérifier que le montant est positif"""
        if value < 0:
            raise serializers.ValidationError("Le montant ne peut pas être négatif.")
        return value

    def create(self, validated_data):
        """Créer un budget avec l'utilisateur connecté"""
        validated_data['user'] = self.context['request'].user
    
        # Safety check for 'montant' field
        montant = validated_data.get('montant')
        if montant is not None:
            validated_data['montant_initial'] = montant
        else:
            
            raise serializers.ValidationError("Le champ 'montant' est requis.")
    
        return super().create(validated_data)
    def update(self, instance, validated_data):
        """Mettre à jour un budget et rompre tous les liens"""
        # Importer les modèles nécessaires
        
        
        # Supprimer toutes les catégories de dépenses liées et leurs dépenses
        categories_liees = CategorieDepense.objects.filter(id_budget=instance)
        categories_liees.delete()  # Cela supprimera aussi les dépenses liées via CASCADE
        
        # Supprimer toutes les dépenses directement liées au budget (sans catégorie)
        depenses_directes = Depense.objects.filter(id_budget=instance, id_cat_depense__isnull=True)
        depenses_directes.delete()
        
        # Supprimer toutes les entrées liées au budget
        entrees_liees = Entree.objects.filter(id_budget=instance)
        entrees_liees.delete()
        
        # Supprimer tous les paiements d'employés liés au budget
        paiements_lies = PaiementEmploye.objects.filter(id_budget=instance)
        paiements_lies.delete()
        
        # Supprimer tous les conseils liés au budget
        conseils_lies = Conseil.objects.filter(id_budget=instance)
        conseils_lies.delete()
        
        # Mettre à jour le montant_initial avec le nouveau montant
        nouveau_montant = validated_data.get('montant', instance.montant)
        validated_data['montant_initial'] = nouveau_montant
        
        return super().update(instance, validated_data)


class CategorieDepenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorieDepense
        fields = ['id', 'nom', 'description', 'montant', 'id_budget', 'user']
        read_only_fields = ('user', 'created_at', 'updated_at')

    def validate_nom(self, value):
        """Vérifier que le nom de la catégorie n'existe pas déjà pour ce budget"""
        budget = self.initial_data.get('id_budget')
        # Si pas de budget spécifié, on ne peut pas valider
        if not budget:
            return value
        # Pour la mise à jour, exclure l'instance actuelle
        queryset = CategorieDepense.objects.filter(id_budget=budget, nom=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "Une catégorie avec ce nom existe déjà pour ce budget."
            )
        return value

    def validate_montant(self, value):
        """Vérifier que le montant est positif"""
        if value < 0:
            raise serializers.ValidationError("Le montant ne peut pas être négatif.")
        return value

    def validate(self, data):
        """Vérifier que le montant de la catégorie ne dépasse pas celui du budget"""
        budget = data.get('id_budget')
        montant = data.get('montant', 0)
        
        # Vérifier que les champs requis sont présents
        if not budget:
            raise serializers.ValidationError({
                'id_budget': "Le budget est requis."
            })
        if montant is None:
            raise serializers.ValidationError({
                'montant': "Le montant est requis."
            })
        
        # Pour la mise à jour, calculer le montant disponible en tenant compte de l'ancien montant
        if self.instance and budget:
            montant_disponible = budget.montant + self.instance.montant_initial
            if montant > montant_disponible:
                raise serializers.ValidationError({
                    'montant': "Le montant de la catégorie ne peut pas dépasser le montant disponible du budget."
                })
        elif budget and montant > budget.montant:
            raise serializers.ValidationError({
                'montant': "Le montant de la catégorie ne peut pas dépasser le montant disponible du budget."
            })
        return data

    def create(self, validated_data):
        """Créer une catégorie et déduire le montant du budget parent"""
        # Vérifier que les données requises sont présentes
        if 'montant' not in validated_data:
            raise serializers.ValidationError("Le champ montant est requis.")
        
        validated_data['user'] = self.context['request'].user
        validated_data['montant_initial'] = validated_data['montant']
        
        # Créer la catégorie
        categorie = super().create(validated_data)
        
        # Déduire le montant du budget parent
        budget = categorie.id_budget
        budget.montant -= categorie.montant
        budget.save()
        
        return categorie

    def update(self, instance, validated_data):
        """Mettre à jour une catégorie avec gestion des montants"""
        budget = instance.id_budget
        ancien_montant = instance.montant_initial
        nouveau_montant = validated_data.get('montant', instance.montant)
        
        # Supprimer toutes les dépenses liées à cette catégorie
        depenses_liees = Depense.objects.filter(id_cat_depense=instance)
        for depense in depenses_liees:
            # Remettre le montant de la dépense dans la catégorie
            instance.montant += depense.montant
            depense.delete()
        
        # Remettre l'ancien montant initial dans le budget
        budget.montant += ancien_montant
        
        # Déduire le nouveau montant du budget
        budget.montant -= nouveau_montant
        budget.save()
        
        # Mettre à jour le montant_initial de la catégorie
        validated_data['montant_initial'] = nouveau_montant
        
        return super().update(instance, validated_data)
    


class DepenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depense
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def validate_montant(self, value):
        """Vérifier que le montant est positif"""
        if value < 0:
            raise serializers.ValidationError("Le montant ne peut pas être négatif.")
        return value
    
    def validate(self, data):
        """Vérifier que le montant de la dépense ne dépasse pas celui de la catégorie"""
        categorie = data.get('id_cat_depense')
        montant = data.get('montant', 0)
        # Vérifier la catégorie si elle existe
        if categorie and montant > categorie.montant:
            raise serializers.ValidationError({
                'montant': "Le montant de la dépense ne peut pas dépasser le montant disponible de la catégorie."
            })
        return data
    
    def create(self, validated_data):
        """Créer une dépense et déduire le montant de la catégorie parent"""
        validated_data['user'] = self.context['request'].user
        # Créer la dépense
        depense = super().create(validated_data)
        # Déduire le montant de la catégorie si elle existe, sinon du budget
        if depense.id_cat_depense:
            categorie = depense.id_cat_depense
            categorie.montant -= depense.montant
            categorie.save()
        # Toujours déduire du budget parent
        budget = depense.id_budget
        budget.montant -= depense.montant
        budget.save()
        return depense

class EntreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entree
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

    def validate_montant(self, value):
        """Vérifier que le montant est positif"""
        if value < 0:
            raise serializers.ValidationError("Le montant ne peut pas être négatif.")
        return value

    def create(self, validated_data):
        """Créer une entrée avec l'utilisateur connecté"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def perform_destroy(self, instance):
        """Supprimer une entrée et déduire le montant du budget"""
        # Déduire le montant du budget lors de la suppression de l'entrée
        budget = instance.id_budget
        budget.montant -= instance.montant
        budget.save()
        
        # Supprimer l'instance
        instance.delete()


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

    def create(self, validated_data):
        """Créer une notification avec l'utilisateur connecté"""
        if 'user' not in validated_data:
            validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ConseilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conseil
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

    def create(self, validated_data):
        """Créer un conseil avec l'utilisateur connecté"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# Sérialiseurs pour les comptes entreprise uniquement
class EmployeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employe
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

    def validate_email(self, value):
        """Validation de l'email"""
        if value and Employe.objects.filter(email=value, user=self.context['request'].user).exists():
            if self.instance and self.instance.email != value:
                raise serializers.ValidationError("Un employé avec cet email existe déjà.")
        return value

    def validate_telephone(self, value):
        """Validation du téléphone"""
        if value and Employe.objects.filter(telephone=value, user=self.context['request'].user).exists():
            if self.instance and self.instance.telephone != value:
                raise serializers.ValidationError("Un employé avec ce numéro de téléphone existe déjà.")
        return value

    def create(self, validated_data):
        """Créer un employé avec l'utilisateur connecté"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PaiementEmployeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaiementEmploye
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at', 'date_paiement')

    def validate_montant(self, value):
        """Vérifier que le montant est positif"""
        if value < 0:
            raise serializers.ValidationError("Le montant ne peut pas être négatif.")
        return value

    def validate(self, data):
        """Vérifier que le budget a suffisamment de fonds"""
        budget = data.get('id_budget')
        montant = data.get('montant', 0)
        
        if budget and montant > budget.montant:
            raise serializers.ValidationError({
                'montant': "Le budget n'a pas suffisamment de fonds pour ce paiement."
            })
        
        return data

    def create(self, validated_data):
        """Créer un paiement et déduire du budget"""
        validated_data['user'] = self.context['request'].user
        
        # Créer le paiement
        paiement = super().create(validated_data)
        
        # Déduire le montant du budget
        budget = paiement.id_budget
        budget.montant -= paiement.montant
        budget.save()
        
        return paiement


class MontantSalaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = MontantSalaire
        fields = '__all__'
        read_only_fields = ('user',)

    def validate(self, data):
        """Valider que tous les montants sont positifs"""
        for field_name, value in data.items():
            if field_name != 'user' and value < 0:
                raise serializers.ValidationError({
                    field_name: "Le montant ne peut pas être négatif."
                })
        return data

    def create(self, validated_data):
        """Créer ou mettre à jour les montants de salaire"""
        validated_data['user'] = self.context['request'].user
        
        # Vérifier si l'utilisateur a déjà une configuration
        existing = MontantSalaire.objects.filter(user=validated_data['user']).first()
        if existing:
            # Mettre à jour l'existant
            for key, value in validated_data.items():
                if key != 'user':
                    setattr(existing, key, value)
            existing.save()
            return existing
        
        return super().create(validated_data)