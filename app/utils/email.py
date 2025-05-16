import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

async def send_email(to_email: str, subject: str, body: str):
    try:
        # Configurer le message
        msg = MIMEMultipart()
        msg['From'] = os.getenv('EMAIL_USER')
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Configurer le serveur SMTP
        smtp_server = aiosmtplib.SMTP(
            hostname='smtp.office365.com',
            port=587,
            use_tls=False
        )
        
        # Connexion au serveur
        await smtp_server.connect()
        await smtp_server.starttls()
        await smtp_server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
        
        # Envoyer l'email
        await smtp_server.send_message(msg)
        await smtp_server.quit()
        
        print(f"✅ Email envoyé à {to_email} avec le sujet : {subject}")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email à {to_email} : {str(e)}")
        raise Exception(f"Failed to send email: {str(e)}")