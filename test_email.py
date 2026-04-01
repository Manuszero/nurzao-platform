import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "Nurzao.Ops@gmail.com"
SENDER_PASSWORD = "rpqe gbgc kmbk khpx"

def test_send():
    try:
        msg = MIMEMultipart()
        msg['Subject'] = "Test Email from Manus"
        msg['From'] = SENDER_EMAIL
        msg['To'] = SENDER_EMAIL
        msg.attach(MIMEText("This is a test email to verify SMTP settings.", 'plain'))
        
        print(f"Connecting to {SMTP_SERVER}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.set_debuglevel(1)
            server.starttls()
            print("Logging in...")
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print("Sending message...")
            server.send_message(msg)
        print("Success!")
        return True
    except Exception as e:
        print(f"Failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_send()
