from email.utils import formataddr
from email.message import EmailMessage
from dotenv import load_dotenv
import smtplib
from stats import get_weekly_data

import sys
sys.path.append('../')
from templates.weekly_usage_summary import WeeklyUsageSummary


if __name__ == "__main__":
  load_dotenv(".chat.env")
  data = get_weekly_data()

  email_generator = WeeklyUsageSummary(data)
  email = email_generator.generate_html_email()
  print(email)

  message = EmailMessage()
  message['From'] = formataddr(('ACIS Admin', 'admin@acis.ufl.edu'))
  message['Subject'] = "Weekly iChatBio Usage Summary"
  message.set_content(email)
  receivers = ["mielliott@ufl.edu", "nitin.goyal@ufl.edu"]
  message['To'] = ", ".join(receivers)

  with smtplib.SMTP('smtp.ufl.edu', 25) as smtp:
    smtp.send_message(message)
