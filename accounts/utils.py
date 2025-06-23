from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from tasks.sendMail import send_email_task


def send_email_with_template(template_name, context, subject, recipient_list, from_email=None):
    """
    Envoie un email en utilisant un template HTML
    
    Args:
        template_name (str): Nom du template (ex: 'emails/password_reset.html')
        context (dict): Contexte pour le template
        subject (str): Sujet de l'email
        recipient_list (list): Liste des destinataires
        from_email (str): Email de l'expéditeur (optionnel)
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    # Rendre le template HTML
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    
    # Envoyer l'email avec EmailMessage pour un meilleur support HTML
    email = EmailMessage(subject, html_message, from_email, recipient_list)
    email.content_subtype = 'html'
    
    # Ajouter des headers pour améliorer la compatibilité HTML
    email.extra_headers = {
        'Content-Type': 'text/html; charset=UTF-8',
        'X-Mailer': 'OptiBudget Email System',
    }
    
    email.send()


def send_email_task_with_template(template_name, context, subject, recipient_list, from_email=None):
    """
    Envoie un email en utilisant un template HTML via Celery
    
    Args:
        template_name (str): Nom du template (ex: 'emails/password_reset.html')
        context (dict): Contexte pour le template
        subject (str): Sujet de l'email
        recipient_list (list): Liste des destinataires
        from_email (str): Email expéditeur (optionnel)
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    # Rendre le template HTML
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    
    # Envoyer l'email via Celery
    send_email_task.delay(
        subject=subject,
        message=plain_message,
        from_email=from_email,
        recipient_list=recipient_list
    )


def send_password_reset_request_email(user, reset_url):
    """Envoie un email de demande de réinitialisation de mot de passe"""
    context = {
        'user': user,
        'reset_url': reset_url
    }
    
    send_email_task_with_template(
        template_name='emails/password_reset_request.html',
        context=context,
        subject='Demande de réinitialisation de mot de passe - OPTIBUDGET',
        recipient_list=[user.email]
    )


def send_password_reset_success_email(user):
    """Envoie un email de confirmation de réinitialisation de mot de passe"""
    context = {
        'user': user
    }
    
    send_email_task_with_template(
        template_name='emails/password_reset_success.html',
        context=context,
        subject='Mot de passe réinitialisé - OPTIBUDGET',
        recipient_list=[user.email]
    )


def send_password_changed_email(user, device_info=None, ip_address=None):
    """Envoie un email de notification de changement de mot de passe"""
    from django.utils import timezone
    
    context = {
        'user': user,
        'change_date': timezone.now(),
        'device_info': device_info,
        'ip_address': ip_address
    }
    
    send_email_task_with_template(
        template_name='emails/password_changed.html',
        context=context,
        subject='Mot de passe modifié - OPTIBUDGET',
        recipient_list=[user.email]
    ) 