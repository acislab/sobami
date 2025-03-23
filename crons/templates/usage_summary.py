from jinja2 import Template
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

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
    def __init__(self, conversations: List[Conversation], users: List[User] = None, kind='Weekly'):
        self.conversations = conversations or []
        self.users = users or []
        self.message_metrics: Dict[str, MessageMetric] = {}
        self.kind = kind

    def format_date(self, date: datetime) -> str:
        return date.strftime("%b %d, %Y at %I:%M %p")

    def get_reporting_period(self) -> Dict[str, str]:
        if self.kind == 'Weekly':
            days = 7
        else:
            days = 1

        start_date = datetime.now().date() - timedelta(days=days)
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
            total_messages += conv["counts"]["user_text_message"]
        return total_messages
    
    def generate_html_email(self) -> str:

        # Jinja2 HTML template
        template_str = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; 
                line-height: 1.5; 
                color: #1a1a1a; 
                margin: 0; 
                padding: 0; 
                background-color: #ffffff;
            }
            .container {
                max-width: 600px;
                margin: 1rem auto;
                padding: 1rem;
                border: 0.0625rem solid #e0e0e0;
                border-radius: 0.5rem;
            }
            .header { 
                text-align: center; 
                margin-bottom: 1.5rem; 
            }
            .header h1 { 
                color: #000000; 
                font-size: 1.4rem; 
                margin-bottom: 0.5rem; 
            }
            .header p { 
                color: #666; 
                font-size: 0.875rem; 
                margin: 0;
            }
            .overview-section {
                background-color: #f9f9f9; 
                border-radius: 0.5rem; 
                padding: 1rem; 
                margin-bottom: 1rem;
            }
            .overview-stats {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-between;
                text-align: center;
            }
            .stat {
                flex: 1;
                min-width: 20%;
                margin: 0.5rem 0;
            }
            .stat-value {
                font-size: 1.5rem; 
                font-weight: bold; 
                color: #000000;
            }
            .stat-label {
                color: #666;
                font-size: 0.8rem;
                margin-top: 0.25rem;
            }
            .table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 1rem;
                table-layout: fixed;
            }
            .table th, 
            .table td {
                border: 1px solid #e0e0e0;
                padding: 0.5rem;
                font-size: 0.875rem;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }
            .table th {
                background-color: #f0f0f0;
                font-weight: 600;
                text-align: left;
            }
            .new-conversations {
                margin-top: 1rem;
            }
            .conversation-card {
                width: full;
                display: flex;
                justify-content: space-between;
                align-items: center;
                background-color: #f0f0f0;
                border-radius: 0.5rem;
                margin-bottom: 0.75rem;
                padding: 0.75rem;
            }
            .conversation-header {
                display: flex;
                flex-direction: column;
            }
            .conversation-meta {
                font-size: 0.75rem;
                color: #666;
                margin-bottom: 0.25rem;
                font-family: monospace;
            }
            .conversation-meta strong {
                color: #000;
            }
            .message-count {
                font-weight: bold;
                padding: 0.25rem 0.5rem;
                border-radius: 1rem;
                font-size: 0.75rem;
                margin-top: 0.25rem;
                display: inline-block;
            }
            .metrics-section {
                margin-top: 1.5rem;
                padding: 0;
            }
            .footer {
                text-align: center;
                color: #666;
                margin-top: 1.5rem;
                font-size: 0.75rem;
            }
            .id-info {
                font-size: 0.75rem;
                color: #666;
                font-family: monospace;
            }
            .id-info p {
                margin: 0 0 0.25rem 0;
            }
            h2 {
                color: #000000; 
                font-size: 1.1rem; 
                margin: 1rem 0 0.75rem 0;
            }
            .empty {
                width: full;
                display: flex;
                justify-content: center;
                color: #666;
                align-items: center;
                font-size: 1.1rem;
            }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>iChatBio - {{ kind }} User Activity</h1>
                    {% if kind == 'Weekly' %}
                        <p><u>{{ period.start }} - {{ period.end }}</u></p>
                    {% else %}
                        <p><u>{{ period.start }}</u></p>
                    {% endif %}
                </div>
                <div class="overview-section">
                    <div class="overview-stats">
                        <div class="stat">
                            <div class="stat-value">{{ total_users }}</div>
                            <div class="stat-label">Sign Ups</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{{ total_conversations }}</div>
                            <div class="stat-label">New Conversations</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{{ total_messages }}</div>
                            <div class="stat-label">User Messages</div>
                        </div>
                    </div>
                </div>

                <h2>New Users</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th width="35%">Email</th>
                            <th width="30%">Profile</th>
                            <th width="35%">Organization</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for user in users %}
                        <tr>
                            <td>{{ user.user_email }}</td>
                            <td>
                                <a href="https://ichatbio.org/admin#/user/{{ user.user_id }}" target="_blank">
                                {{ user.username }}
                                </a>
                            </td>
                            <td>{{ user.organization }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>

                <h2>User Conversations</h2>
                <div class="new-conversations">
                    {% for conv in conversations %}
                    <div class="conversation-card">
                        <div class="conversation-header">
                            <div class="id-info">
                                <p><strong>User:</strong> 
                                    <a href="https://ichatbio.org/admin#/user/{{ conv.user_id }}" target="_blank">
                                    <u>{{ conv.username }}</u>
                                    </a>
                                </p>
                                <p><strong>Conversation ID:</strong> {{ conv.conv_id }}</p>
                                <p><strong>Date:</strong> {{ conv.last_message_created }}</p>
                            </div>
                        </div>
                        <div class="message-count">{{ conv.counts["user_text_message"] }} user messages</div>
                    </div>
                    {% endfor %}
                </div>

                <div class="metrics-section overview-section">
                    <h2>Messaging Metrics</h2>
                    <table class="table">
                        <thead>
                            <tr>
                                <th width="70%">Message Type</th>
                                <th width="30%">Count</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for type, metric in message_metrics.items() %}
                            <tr>
                                <td>{{ type }}</td>
                                <td>{{ metric.count }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                <div class="footer">
                    <p>This is an automated summary generated on {{ generation_date }}</p>
                    <p>&copy; 2025 <a href="https://www.acis.ufl.edu" target="_blank">www.acis.ufl.edu</a></p>         
                </div>
            </div>
        </body>
        </html>
        """

        template = Template(template_str)
        return template.render(
            period=self.get_reporting_period(),
            total_users=len(self.users),
            total_messages=self.get_total_messages(),
            message_metrics=self.analyze_message_metrics(),
            users=self.users,
            total_conversations=len(self.conversations),
            conversations=self.conversations,
            kind=self.kind,
            generation_date=datetime.now().strftime("%B %d, %Y")
        )