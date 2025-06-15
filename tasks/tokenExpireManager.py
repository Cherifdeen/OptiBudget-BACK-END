from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from rest_framework.authtoken.models import Token

@shared_task
def clean_expired_tokens():
    """Supprime les tokens expirés (24h)"""
    expiration_time = timezone.now() - timedelta(hours=24)
    expired_count = Token.objects.filter(created__lt=expiration_time).count()
    Token.objects.filter(created__lt=expiration_time).delete()
    return f"Supprimé {expired_count} tokens expirés"