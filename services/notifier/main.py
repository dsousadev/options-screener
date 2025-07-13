import os
import time
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

def poll_for_jobs():
    """Polls the notifications table for pending jobs."""
    print("Starting notifier service...")
    print(f"Database URL: {os.environ.get('DATABASE_URL', 'NOT SET')}")
    print(f"SendGrid API Key: {'SET' if os.environ.get('SENDGRID_API_KEY') else 'NOT SET'}")
    print(f"From Email: {os.environ.get('FROM_EMAIL', 'NOT SET')}")
    
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    # Important: autocommit=True to ensure updates are written immediately
    conn.autocommit = True
    cursor = conn.cursor()

    while True:
        cursor.execute("SELECT id, recipient_email, subject, body FROM notifications WHERE status = 'pending' LIMIT 10;")
        jobs = cursor.fetchall()
        
        if not jobs:
            print("Notifier heartbeat: No pending notifications found.")
        else:
            print(f"Found {len(jobs)} pending notification jobs")
        
        for job in jobs:
            job_id, email, subject, body = job
            print(f"Processing notification job {job_id} for {email}...")
            
            if send_notification(email, subject, body):
                cursor.execute("UPDATE notifications SET status = 'sent' WHERE id = %s;", (job_id,))
                print(f"Successfully sent notification {job_id}")
            else:
                cursor.execute("UPDATE notifications SET status = 'failed' WHERE id = %s;", (job_id,))
                print(f"Failed to send notification {job_id}")

        time.sleep(10) # Poll every 10 seconds

if __name__ == "__main__":
    poll_for_jobs()
