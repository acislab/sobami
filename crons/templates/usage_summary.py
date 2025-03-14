from jinja2 import Template
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

@dataclass
class Message:
    id: str
    type: str
    value: str
    created: datetime

@dataclass
class MessageMetric:
    type: str
    count: int = 0
    description: str = ""

@dataclass
class User:
    id: str
    name: str = ""
    given_name: str = ""
    email: str = ""
    organization: str = ""


class UsageSummary:
    def __init__(self, data: Dict[str, Dict], users_data: List[User] = None, kind='Weekly'):
        self.data = data
        self.users_data = users_data or []
        self.message_metrics: Dict[str, MessageMetric] = {}
        self.kind = kind

    def format_date(self, date: datetime) -> str:
        return date.strftime("%b %d, %Y at %I:%M %p")

    def get_reporting_period(self) -> Dict[str, str]:
        if self.kind == 'Weekly':
            days = 7
        else:
            days = 0
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return {
            "start": start_date.strftime("%B %d, %Y"),
            "end": end_date.strftime("%B %d, %Y")
        }

    def analyze_message_metrics(self) -> Dict[str, MessageMetric]:
        """Analyze and categorize message types."""
        metrics = {
            "user_text_message": MessageMetric(
                type="user_text_message", 
                description="Standard User Text Messages"
            ),
            "ai_text_message": MessageMetric(
                type="ai_text_message", 
                description="Standard AI Responses"
            ),
            "ai_processing_message": MessageMetric(
                type="ai_processing_message",
                description="AI Processing Messages"
            )
            # Add more metrics if needed
        }

        # Initialize metrics
        self.message_metrics = metrics.copy()

        # Count messages across all users and their conversations
        for user_id, user_data in self.data.items():
            for conv_id, conv_data in user_data.get("conversations", {}).items():
                for message in conv_data.get("messages", []):
                    msg_type = message.get("type")
                    if msg_type in self.message_metrics:
                        self.message_metrics[msg_type].count += 1

        return self.message_metrics
    
    def generate_html_email(self) -> str:
        period = self.get_reporting_period()
        total_users = len(self.data)

        total_messages = 0
        for user_id, user_data in self.data.items():
            for conv_id, conv_data in user_data.get("conversations", {}).items():
                total_messages += len(conv_data.get("messages", []))

        message_metrics = self.analyze_message_metrics()

        user_conversations = []
        for user_id, user_data in self.data.items():
            for conv_id, conv_data in user_data.get("conversations", {}).items():
                messages = [
                    Message(
                        id=msg.get("id", ""),
                        type=msg.get("type", ""),
                        value=msg.get("value", ""),
                        created=datetime.fromisoformat(msg.get("created", datetime.now().isoformat()))
                    )
                    for msg in conv_data.get("messages", [])
                ]
                
                if messages:
                    user_conversations.append({
                        "user_id": user_id,
                        "conversation_id": conv_id,
                        "username": user_id,  # Keeping existing field for compatibility
                        "join_date": self.format_date(messages[0].created),
                        "message_count": len(messages),
                        "messages": messages
                    })
        total_conversation = len(user_conversations)

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
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>iChatBio - {{ kind }} Summary: New User Activity</h1>
                    {% if kind == 'Weekly' %}
                        <p><u>{{ period.start }} - {{ period.end }}</u></p>
                    {% else %}
                        <p><u>{{ period.end }}</u></p>
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
                            <div class="stat-label">Conversations</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{{ total_messages }}</div>
                            <div class="stat-label">Messages</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">{{ (total_messages / total_users)|round(1) }}</div>
                            <div class="stat-label">Avg. Messages/User</div>
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
                        {% for user in users_data %}
                        <tr>
                            <td>{{ user.email }}</td>
                            <td>
                                <a href="https://ichatbio.org/admin#/user/{{ user.user_id }}" target="_blank">
                                {{ user.given_name }}
                                </a>
                            </td>
                            <td>{{ user.organization }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>

                <h2>User Conversations</h2>
                <div class="new-conversations">
                    {% for conv in user_conversations %}
                    <div class="conversation-card">
                        <div class="conversation-header">
                            <div class="id-info">
                                <p><strong>Username:</strong> {{ conv.username }}</p>
                                <p><strong>Joined:</strong> {{ conv.join_date }}</p>
                                <p><strong>Conversation ID:</strong> {{ conv.conversation_id }}</p>
                            </div>
                        </div>
                        <div class="message-count">{{ conv.message_count }} messages</div>
                    </div>
                    {% endfor %}
                </div>

                <div class="metrics-section overview-section">
                    <h2>Messaging Metrics</h2>
                    <table class="table">
                        <thead>
                            <tr>
                                <th width="30%">Message Type</th>
                                <th width="20%">Count</th>
                                <th width="50%">Description</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for type, metric in message_metrics.items() %}
                            <tr>
                                <td>{{ type }}</td>
                                <td>{{ metric.count }}</td>
                                <td>{{ metric.description }}</td>
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
            period=period,
            total_users=total_users,
            total_messages=total_messages,
            message_metrics=message_metrics,
            user_conversations=user_conversations,
            total_conversations=total_conversation,
            users_data=self.users_data,
            kind=self.kind,
            generation_date=datetime.now().strftime("%B %d, %Y")
        )