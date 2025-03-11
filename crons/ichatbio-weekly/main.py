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

from stats import get_weekly_data
sys.path.append('../')
from templates.weekly_usage_summary import WeeklyUsageSummary

# Logging Setup
log_file = 'ichatbio_email_service.weekly.log'
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

# Fetch weekly summary data
data, users_data = get_weekly_data()
logger.info("Weekly summary data fetched from DB")

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
print(data, users_data)
email_generator = WeeklyUsageSummary(data, users_data)
email_content = email_generator.generate_html_email()
logger.info("Email generated")

# Prepare email
message = MIMEMultipart("alternative")
sender_name = os.getenv("EMAIL_FROM_NAME",)
sender_email = os.getenv("EMAIL_FROM_EMAIL")
message['From'] = formataddr((sender_name, sender_email))
message['Subject'] = os.getenv("EMAIL_SUBJECT", "Weekly iChatBio Usage Summary")
message['To'] = ", ".join(recipients)
message.attach(MIMEText(email_content, "html"))

# Retry settings
retry_attempts = int(os.getenv("RETRY_ATTEMPTS", 3))
retry_delay = int(os.getenv("RETRY_DELAY", 5))

# Send email with retries
for attempt in range(1, retry_attempts + 1):
    try:
        logger.info(f"Sending email to {len(recipients)} recipients (attempt {attempt})")
        with smtplib.SMTP(os.getenv("SMTP_SERVER"), os.getenv("SMTP_PORT")) as smtp:
            smtp.sendmail(sender_email, recipients, message.as_string())
        logger.info(f"Email sent successfully to {len(recipients)} recipients")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to send email (attempt {attempt}): {e}")
        if attempt < retry_attempts:
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

logger.error("All attempts to send email failed")
sys.exit(1)
