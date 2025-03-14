from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from dotenv import load_dotenv
import smtplib
import logging
import datetime
import time
import os
import json
import sys
import argparse

from stats import get_data
sys.path.append('../')
from templates.usage_summary import UsageSummary

parser = argparse.ArgumentParser('iChatBio Usage Summary Service')
parser.add_argument('--kind', dest="kind", choices=['Daily', 'Weekly'], type=str, help='Choose a summary duration')
args = parser.parse_args()
kind = args.kind

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
logger = logging.getLogger(log_file)
logger.info(f"Logging initialized. Saving logs to {log_file}")

logger.info("\n" + "=" * 50)
logger.info(f"New job execution started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info("=" * 50 + "\n")

# Load environment variables
load_dotenv(".chat.env")
logger.info("Loaded .chat.env")

# Fetch summary data
days = 1 if kind == 'Daily' else 7
data, users_data = get_data(days=days)
logger.info(f"{kind} summary data fetched from DB")

# Load recipients list
recipients_file = os.getenv("RECIPIENTS_FILE", "recipients.json")
with open(recipients_file, "r") as file:
    receivers = json.load(file)

recipients = receivers.get("recipients", [])
if not recipients:
    logger.error("No recipients configured. Email not sent.")
    sys.exit(1)

logger.info(f"Sending email to {len(recipients)} recipients")

# Generate email content
email_generator = UsageSummary(data, users_data, kind=kind)
email_content = email_generator.generate_html_email()
print(email_content)
logger.info("Email generated")

# # Prepare email
# message = MIMEMultipart("alternative")
# sender_name = os.getenv("EMAIL_FROM_NAME",)
# sender_email = os.getenv("EMAIL_FROM_EMAIL")
# message['From'] = formataddr((sender_name, sender_email))
# message['Subject'] = os.getenv("EMAIL_SUBJECT", f"{kind} iChatBio Usage Summary")
# message['To'] = ", ".join(recipients)
# message.attach(MIMEText(email_content, "html"))

# # Retry settings
# retry_attempts = int(os.getenv("RETRY_ATTEMPTS", 3))
# retry_delay = int(os.getenv("RETRY_DELAY", 5))

# # Send email with retries
# for attempt in range(1, retry_attempts + 1):
#     try:
#         logger.info(f"Sending email to {len(recipients)} recipients (attempt {attempt})")
#         with smtplib.SMTP(os.getenv("SMTP_SERVER"), os.getenv("SMTP_PORT")) as smtp:
#             smtp.sendmail(sender_email, recipients, message.as_string())
#         logger.info(f"Email sent successfully to {len(recipients)} recipients")
#         sys.exit(0)
#     except Exception as e:
#         logger.error(f"Failed to send email (attempt {attempt}): {e}")
#         if attempt < retry_attempts:
#             logger.info(f"Retrying in {retry_delay} seconds...")
#             time.sleep(retry_delay)

# logger.error("All attempts to send email failed")
# sys.exit(1)
