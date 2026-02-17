from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict

from jinja2 import Environment, FileSystemLoader
import os

@dataclass
class Service:
    name: str
    status: bool

@dataclass
class Conversation:
    user_id: str
    username: str
    conv_id: str
    total_message_count: int
    last_message_created: datetime
    counts: Dict[str, int]

@dataclass
class MessageMetric:
    type: str
    count: int = 0

@dataclass
class User:
    user_id: str
    username: str = ""
    user_email: str = ""
    organization: str = ""

class UsageSummary:
    def __init__(self, services: List[Service], conversations: List[Conversation], users: List[User] = None, days=1):
        self.services = services
        self.conversations = conversations or []
        self.users = users or []
        self.message_metrics: Dict[str, MessageMetric] = {}
        self.days = days

    def format_date(self, date: datetime) -> str:
        return date.strftime("%b %d, %Y at %I:%M %p")

    def get_reporting_period(self) -> Dict[str, str]:
        start_date = datetime.now().date() - timedelta(days=self.days)
        end_date = datetime.now().date() - timedelta(1)
        return {
            "start": start_date.strftime("%B %d, %Y"),
            "end": end_date.strftime("%B %d, %Y")
        }

    def analyze_message_metrics(self) -> Dict[str, MessageMetric]:
        metrics: Dict[str, MessageMetric] = {}
        for conv in self.conversations:
            for message_type, count in conv["counts"].items():
                if message_type not in metrics:
                    metrics[message_type] = MessageMetric(
                        type=message_type,
                        count=count,
                    )
                else:
                    metrics[message_type].count += count

        self.message_metrics = metrics.copy()
        return self.message_metrics
    
    def get_total_messages(self):
        total_messages = 0
        for conv in self.conversations:
            total_messages += conv["counts"]["user_message"]
        return total_messages
    
    def generate_html_email(self) -> str:
        template_dir = os.path.join(os.path.dirname(__file__))
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("summary.html.j2")

        return template.render(
            period=self.get_reporting_period(),
            total_users=len(self.users),
            total_messages=self.get_total_messages(),
            message_metrics=self.analyze_message_metrics(),
            services=self.services,
            users=self.users,
            total_conversations=len(self.conversations),
            conversations=self.conversations,
            frequency="Daily" if self.days == 1 else f"{self.days}-Day",
            generation_date=datetime.now().strftime("%B %d, %Y")
        )