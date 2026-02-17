import argparse
import datetime
import logging
import os
import smtplib
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from dotenv import load_dotenv

import services
from stats import get_data
from templates.usage_summary import UsageSummary

load_dotenv()

parser = argparse.ArgumentParser('iChatBio Usage Summary Service')
parser.add_argument('--kind', dest="days", default=1, type=int, help='Choose a summary duration')
args = parser.parse_args()
days = args.days

# Logging Setup
log_file = 'ichatbio_email_service.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logging.info(f"Logging initialized. Saving logs to {log_file}")

logging.info("\n" + "=" * 50)
logging.info(f"New job execution started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logging.info("=" * 50 + "\n")

# Fetch summary data
conversations, new_users = get_data(days=days)
logging.info(f"{days} day(s) of data fetched from DB")

# Check online services
service_defs = os.getenv("SERVICES", "").strip().split("\n")
service_statuses = [{"name": agent, "status": status} for agent, status in services.check_all(service_defs)]

# Load recipients list
recipients = os.getenv("RECIPIENTS", "").split(",")

if not recipients:
    logging.error("No recipients configured. Email not sent.")
    sys.exit(1)

logging.info(f"Sending email to {len(recipients)} recipients")

# Generate email content
email_generator = UsageSummary(service_statuses, conversations, new_users, days=days)
email_content = email_generator.generate_html_email()
logging.info("Email generated")

# Prepare email
message = MIMEMultipart("alternative")
sender_name = os.getenv("EMAIL_FROM_NAME",)
sender_email = os.getenv("EMAIL_FROM_EMAIL")
message['From'] = formataddr((sender_name, sender_email))
message['Subject'] = f"iChatBio - {'Daily' if days == 1 else f'{days}-Day'} Summary"
message['To'] = ", ".join(recipients)
message.attach(MIMEText(email_content, "html"))

# Retry settings
retry_attempts = int(os.getenv("RETRY_ATTEMPTS", 3))
retry_delay = int(os.getenv("RETRY_DELAY", 5))

# Send email with retries
for attempt in range(1, retry_attempts + 1):
    try:
        logging.info(f"Sending email to {len(recipients)} recipients (attempt {attempt})")
        with smtplib.SMTP(os.getenv("SMTP_SERVER"), os.getenv("SMTP_PORT")) as smtp:
            smtp.sendmail(sender_email, recipients, message.as_string())
        logging.info(f"Email sent successfully to {len(recipients)} recipients")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Failed to send email (attempt {attempt}): {e}")
        if attempt < retry_attempts:
            logging.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

logging.error("All attempts to send email failed")
sys.exit(1)
