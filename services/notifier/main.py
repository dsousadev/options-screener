import os
import psycopg2
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_notification(email, subject, body):
    """Sends an email using the SendGrid API."""
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        message = Mail(
            from_email=os.environ.get('FROM_EMAIL'),
            to_emails=email,
            subject=subject,
            html_content=body)
        response = sg.send(message)
        print(f"Sent notification to {email}, status: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending notification to {email}: {e}")
        return False

def send_notification_job(email, subject, body):
    """
    Job function that will be called by the RQ worker.
    This replaces the polling mechanism.
    """
    print(f"Notifier processing job: sending email to {email}")
    
    if send_notification(email, subject, body):
        print(f"Successfully sent notification to {email}")
        return True
    else:
        print(f"Failed to send notification to {email}")
        return False
