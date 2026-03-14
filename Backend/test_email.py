from dotenv import load_dotenv
import os, sys

load_dotenv(".env")
SENDER = os.environ.get("ALERT_EMAIL_SENDER")
PASSWORD = os.environ.get("ALERT_EMAIL_PASSWORD")
RECIPIENT = os.environ.get("ALERT_EMAIL_RECIPIENT")

if not SENDER or not PASSWORD or not RECIPIENT:
    sys.exit(1)

test_anomaly = {
    "type": "Manual Email Test",
    "detail": "If you are reading this, the Python SMTP script successfully connected to your Gmail account and fired an alert. The App Password is working perfectly!"
}

# The AI needs enterprise context
mock_enterprise_data = {
    "business_kpis": {"revenue_today_usd": 1200000, "estimated_loss_today_usd": 4000},
    "logistics": {"delayed": 47}
}

from main import _send_critical_email_alert

try:
    _send_critical_email_alert(test_anomaly, mock_enterprise_data)
except Exception as e:
    print(f"Error details: {e}")
