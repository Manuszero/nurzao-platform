from flask import Flask, render_template_string, request, jsonify
import os
from threading import Thread
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_html_content():
    """Read HTML content from index.html dynamically"""
    try:
        if os.path.exists('index.html'):
            with open('index.html', 'r', encoding='utf-8') as f:
                return f.read()
        return "<h1>Nurzao Platform - Under Construction</h1>"
    except Exception as e:
        logger.error(f"Error loading index.html: {str(e)}")
        return f"<h1>Error loading page: {str(e)}</h1>"

# Email Configuration - Use environment variables for security
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'Nurzao.Ops@gmail.com')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD', 'ckec efev qdcn diim')

# Global check for credentials at startup
if not SENDER_EMAIL or not SENDER_PASSWORD:
    logger.warning("WARNING: SENDER_EMAIL or SENDER_PASSWORD environment variables are not set!")

OPS_EMAIL = os.environ.get('OPS_EMAIL', 'Nurzao.HQ@gmail.com')
WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '+249110110054')

@app.route('/')
def index():
    return render_template_string(get_html_content())

def send_email(to_email, subject, body):
    """Send email synchronously with detailed error handling"""
    try:
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            logger.error("Email credentials not configured. Cannot send email.")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['X-Priority'] = '1'  # High priority
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        logger.info(f"Attempting to send email to {to_email} via {SMTP_SERVER}:{SMTP_PORT}")
        
        # Using context manager for SMTP to ensure connection is closed
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            result = server.send_message(msg)
            logger.info(f"Email sent successfully to {to_email} - Result: {result}")
            return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Authentication failed: {str(e)}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error when sending to {to_email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"CRITICAL: Failed to send email to {to_email}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

@app.route('/api/contact', methods=['POST'])
def handle_contact():
    """Handle contact form submissions"""
    try:
        data = request.json
        logger.info(f"Received contact form submission: {data}")
        
        required_fields = ['name', 'email', 'phone', 'service', 'details']
        if not all(key in data for key in required_fields):
            return jsonify({"status": "error", "message": "بيانات غير كاملة"}), 400
        
        # 1. Prepare email for OPS
        subject_ops = f"طلب استشارة جديد من {data['name']}"
        body_ops = f"""
        <html dir="rtl">
        <body style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6;">
            <h2 style="color: #6366f1;">طلب استشارة جديد 🎯</h2>
            <div style="background: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
                <p><strong>الاسم:</strong> {data['name']}</p>
                <p><strong>البريد:</strong> {data['email']}</p>
                <p><strong>الهاتف:</strong> {data['phone']}</p>
                <p><strong>الخدمة:</strong> {data['service']}</p>
                <p><strong>التفاصيل:</strong><br>{data['details']}</p>
            </div>
            <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 20px;">تم الإرسال عبر منصة Nurzao</p>
        </body>
        </html>
        """
        
        # 2. Prepare confirmation for customer
        subject_cust = "تم استقبال طلبك - Nurzao"
        body_cust = f"""
        <html dir="rtl">
        <body style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6;">
            <h2 style="color: #6366f1;">شكراً لك {data['name']}! ✅</h2>
            <p>لقد تلقينا طلبك بخصوص <strong>{data['service']}</strong> بنجاح.</p>
            <p>سيقوم فريق العمليات لدينا بمراجعة طلبك والتواصل معك في أقرب وقت ممكن.</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <p style="font-size: 0.9rem;">فريق Nurzao للتمكين الرقمي</p>
        </body>
        </html>
        """
        
        # Send emails in background threads to avoid timeout
        logger.info("Starting background email threads")
        ops_thread = Thread(target=send_email, args=(OPS_EMAIL, subject_ops, body_ops), daemon=True)
        cust_thread = Thread(target=send_email, args=(data['email'], subject_cust, body_cust), daemon=True)
        
        ops_thread.start()
        cust_thread.start()
        
        # Return success immediately without waiting for emails to complete
        logger.info(f"Contact form response sent immediately for {data['name']} - emails will send in background")
        return jsonify({
            "status": "success",
            "message": "تم إرسال طلبك بنجاح! سيتم إرسال تأكيد على بريدك قريباً.",
            "whatsapp_data": {
                "phone": WHATSAPP_NUMBER,
                "name": data['name'],
                "service": data['service'],
                "phone_number": data['phone']
            }
        })
    
    except Exception as e:
        logger.error(f"Error handling contact form: {str(e)}")
        return jsonify({"status": "error", "message": "حدث خطأ داخلي"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
