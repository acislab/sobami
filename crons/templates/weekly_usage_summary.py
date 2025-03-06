from jinja2 import Template
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict

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

class WeeklyUsageSummary:
    def __init__(self, weekly_data: Dict[str, Dict]):
        self.weekly_data = weekly_data
        self.message_metrics: Dict[str, MessageMetric] = {}

    def format_date(self, date: datetime) -> str:
        return date.strftime("%b %d, %Y at %I:%M %p")

    def get_reporting_period(self) -> Dict[str, str]:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        return {
            "start": start_date.strftime("%B %d, %Y"),
            "end": end_date.strftime("%B %d, %Y")
        }

    def get_conversation_preview(self, messages: List[Message]) -> str:
        if not messages:
            return "No messages"

        first_user_message = next((m for m in messages if m.type == "user_text_message"), None)
        first_ai_response = next((m for m in messages if m.type == "ai_text_message"), None)

        if first_user_message and first_ai_response:
            return f'User: "{first_user_message.value[:30]}..." AI: "{first_ai_response.value[:30]}..."'
        return ""

    def analyze_message_metrics(self) -> Dict[str, MessageMetric]:
        """Analyze and categorize message types."""
        # Define default message types to track
        default_metrics = {
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
        self.message_metrics = default_metrics.copy()

        # Count messages across all users and their conversations
        for user_id, user_data in self.weekly_data.items():
            for conv_id, conv_data in user_data.get("conversations", {}).items():
                for message in conv_data.get("messages", []):
                    msg_type = message.get("type")
                    if msg_type in self.message_metrics:
                        self.message_metrics[msg_type].count += 1

        return self.message_metrics
    

    def generate_html_email(self) -> str:
        period = self.get_reporting_period()
        total_users = len(self.weekly_data)

        total_messages = 0
        for user_id, user_data in self.weekly_data.items():
            for conv_id, conv_data in user_data.get("conversations", {}).items():
                total_messages += len(conv_data.get("messages", []))

        message_metrics = self.analyze_message_metrics()

        user_conversations = []
        for user_id, user_data in self.weekly_data.items():
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
                        "preview": self.get_conversation_preview(messages),
                        "messages": messages
                    })

        # Jinja2 HTML template
        template_str = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; 
                line-height: 1.6; 
                color: #1a1a1a; 
                max-width: 50rem; 
                margin: 2rem; 
                padding: 1.25rem; 
                background-color: #ffffff;
                border: 0.0625rem solid #e0e0e0;
                border-radius: 0.5rem;
            }
            .header { 
                text-align: center; 
                margin-bottom: 1.875rem; 
            }
            .header h1 { 
                color: #000000; 
                font-size: 1.5rem; 
                margin-bottom: 0.625rem; 
            }
            .header p { 
                color: #666; 
                font-size: 0.875rem; 
            }
            .overview-section {
                background-color: #f9f9f9; 
                border-radius: 0.5rem; 
                padding: 1.25rem; 
                margin-bottom: 1.25rem;
            }
            .overview-stats {
                display: flex;
                justify-content: space-between;
                text-align: center;
            }
            .stat {
                flex: 1;
            }
            .stat-value {
                font-size: 1.75rem; 
                font-weight: bold; 
                color: #000000;
            }
            .stat-label {
                color: #666;
                font-size: 0.8rem;
                margin-top: 0.3125rem;
            }
            .new-conversations {
                margin-top: 1.25rem;
            }
            .conversation-item {
                background-color: #ffffff;
                border: 0.0625rem solid #e0e0e0;
                border-radius: 0.5rem;
                margin-bottom: 0.9375rem;
                box-shadow: 0 0.0625rem 0.1875rem rgba(0,0,0,0.05);
            }
            .conversation-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: pointer;
                padding: 1.75rem;
            }
            .conversation-header h3 {
                margin: 0;
                font-size: 1rem;
                color: #000000;
            }
            .conversation-header .message-meta {
                display: flex;
                align-items: center;
                color: #666;
                font-size: 0.875rem;
            }
            .message-meta {
                padding-right: 0.9375rem;
            }
            .conversation-preview {
                margin-top: 0.25rem;
                font-size: 0.875rem;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .conversation-content {
                display: none;
                padding: 0.9375rem;
                border-top: 0.0625rem solid #e0e0e0;
            }
            .conversation-content.active {
                display: block;
                padding: 1.75rem;
            }
            .message {
                margin-bottom: 0.75rem;
                padding: 1rem;
                border-radius: 0.5rem;
            }
            .message-user {
                background-color: #f0f6ff;
                color: #1a1a1a;
            }
            .message-ai {
                background-color: #f0f0f0;
                color: #1a1a1a;
            }
            .message-date {
                color: #666;
                font-size: 0.75rem;
                margin-top: 0.3125rem;
            }
            .message-id {
                color: #666;
                font-size: 0.75rem;
                font-family: monospace;
            }
            .user {
                text-align: right;
            }
            .metrics-section {
                margin-top: 1.875rem;
                padding: 0;
            }
            .metrics-table {
                width: 100%;
                border-collapse: collapse;
            }
            .metrics-table th, 
            .metrics-table td {
                border: 0.0625rem solid #e0e0e0;
                padding: 0.625rem;
                text-align: left;
            }
            .metrics-table th {
                background-color: #f9f9f9;
                color: #000000;
            }
            .footer {
                text-align: center;
                color: #666;
                margin-top: 1.875rem;
                font-size: 0.75rem;
            }
            .expand-icon {
                margin-left: 0.625rem;
            }
            .id-info {
                font-size: 0.75rem;
                color: #666;
                font-family: monospace;
            }
            .id-info p {
                margin: 0;
            }
            </style>
            <script>
            function toggleConversation(id) {
                const conversationItem = document.getElementById(id);
                const content = conversationItem.querySelector('.conversation-content');
                const icon = conversationItem.querySelector('.expand-icon');
                
                content.classList.toggle('active');
                icon.style.transform = content.classList.contains('active') 
                ? 'rotate(180deg)' 
                : 'rotate(0deg)';
            }
            </script>
        </head>
        <body>
            <div class="header">
            <h1>iChatBio - Weekly Usage Summary</h1>
            <p>{{ period.start }} - {{ period.end }}</p>
            </div>

            <div class="overview-section">
            <div class="overview-stats">
                <div class="stat">
                <div class="stat-value">{{ total_users }}</div>
                <div class="stat-label">New Users</div>
                </div>
                <div class="stat">
                <div class="stat-value">{{ total_messages }}</div>
                <div class="stat-label">Total Messages</div>
                </div>
                <div class="stat">
                <div class="stat-value">{{ (total_messages / total_users)|round(1) }}</div>
                <div class="stat-label">Avg. Messages/User</div>
                </div>
            </div>
            </div>

            <div class="new-conversations">
            <h2 style="color: #000000; font-size: 1.25rem; margin-bottom: 0.9375rem;">New User Conversations</h2>
            {% for conv in user_conversations %}
            <div id="{{ conv.user_id }}-{{ conv.conversation_id }}" class="conversation-item">
                <div class="conversation-header" onclick="toggleConversation('{{ conv.user_id }}-{{ conv.conversation_id }}')">
                <div>
                    <div class="id-info">
                        <p style="font-weight: bold; color: #000000">Username: {{ conv.username }}</p>
                        <p style="color: #666; margin: 0px; font-size:0.75rem">Joined: {{ conv.join_date }}</p>
                        <p>Conversation ID: {{ conv.conversation_id }}</p>
                    </div>
                    <div class="conversation-preview">{{ conv.preview }}</div>
                </div>
                <div class="message-meta">
                    {{ conv.message_count }} messages
                    <svg class="expand-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </div>
                </div>
                <div class="conversation-content">
                {% for msg in conv.messages %}
                <div class="message {{ 'message-user user' if msg.type == 'user_text_message' else 'message-ai' }}">
                    {% if msg.type == 'ai_processing_message' %}
                        <div style="color: #666; font-style: italic;">Processing: {{ msg.value.summary if msg.value is mapping and msg.value.summary else msg.value }}</div>
                    {% else %}
                        {{ msg.value }}
                    {% endif %}
                    <div class="message-date">{{ msg.created.strftime('%b %d, %Y at %I:%M %p') }}</div>
                    <div class="message-id">Message ID: {{ msg.id }}</div>
                </div>
                {% endfor %}
                </div>
            </div>
            {% endfor %}
            </div>

            <div class="metrics-section overview-section">
            <h2 style="color: #000000; font-size: 1.25rem; margin-bottom: 0.9375rem;">Metrics</h2>
            <table class="metrics-table">
                <thead>
                <tr>
                    <th>Message Type</th>
                    <th>Count</th>
                    <th>Description</th>
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
            <p>&copy; 2025 <a href="https://www.acis.ufl.edu" class="footer" target="_blank">www.acis.ufl.edu</a></p>         
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
            generation_date=datetime.now().strftime("%B %d, %Y")
        )
