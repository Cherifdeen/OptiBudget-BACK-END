from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_email_task(subject, message, from_email, recipient_list):
    try:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        print(f"Email sent to {recipient_list} with subject: {subject}")
        return "Email sent successfully"
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return f"Failed to send email: {str(e)}"
    
