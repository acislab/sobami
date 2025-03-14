from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import logging
import os
import psycopg2
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger('ichatbio_email_service.weekly.log')

@dataclass
class User:
    id: str
    name: str = ""
    given_name: str = ""
    email: str = ""
    organization: str = ""

# ================================================================== #
# Queries
# ================================================================== #
def get_db_connection(connection_string: str) -> psycopg2.extensions.connection:
    try:
        conn = psycopg2.connect(connection_string)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


def get_new_users(connection_string: str, days: int = 7) -> Dict[str, str]:
    """
    Fetch users who registered within the last specified number of days.
    Returns a dictionary mapping user_id to username/email.
    
    Args:
        connection_string: PostgreSQL connection string
        days: Number of days to look back
        
    Returns:
        Dictionary with user_id as keys and display names as values
    """
    try:
        conn = get_db_connection(connection_string)
        cur = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT 
            u.id AS user_id, 
            u.email AS user_email,
            u.given_name AS username
        FROM users u
        WHERE u.created >= %s
        ORDER BY u.created DESC;
        """
        
        cur.execute(query, (cutoff_date,))
        
        # Create user mapping
        user_map = {}
        for user_id, user_email, username in cur.fetchall():
            # Use username if available, otherwise email
            display_name = username if username else user_email
            user_map[user_id] = display_name
        
        cur.close()
        conn.close()
        
        logger.info(f"Found {len(user_map)} new users in the last {days} days")
        return user_map
    
    except Exception as e:
        logger.error(f"Error fetching new users: {e}")
        raise


def get_nested_data(user_map: Dict[str, str], connection_string: str) -> Dict[str, Any]:
    """
    Queries the database for conversations and messages linked to each user_id
    and returns a nested JSON structure with usernames.

    Messages are sorted in order of creation.
    
    Args:
        user_map: Dictionary mapping user_ids to display names
        connection_string: PostgreSQL connection string
        
    Returns:
        Nested dictionary with conversation data organized by user
        
    Structure:
    {
      "username": {
        "conversations": {
          "conversation_id": {
            "messages": [
              {
                "id": "message_id",
                "type": "message_type",
                "value": "message_content",
                "created": "timestamp"
              },
              ...
            ]
          }
        }
      }
    }
    """
    try:
        # Check if we have users to process
        if not user_map:
            logger.warning("No users provided to process")
            return {}
            
        conn = get_db_connection(connection_string)
        cur = conn.cursor()

        user_ids = list(user_map.keys())
        
        logger.info(f"Querying conversations for {len(user_ids)} users")

        query = """
        SELECT 
            u.id AS user_id,
            c.id AS conversation_id,
            m.id AS message_id,
            m.frontend_messages,
            m.created AS message_created
        FROM users u
        JOIN conversations c ON u.id = c.user_id
        JOIN messages m ON c.id = m.conversation_id
        WHERE u.id = ANY(%s)
        ORDER BY u.id, c.created, m.created;
        """

        cur.execute(query, (user_ids,))

        result = {}
        message_count = 0
        for row in cur.fetchall():
            user_id, conv_id, msg_id, frontend_msgs, msg_created = row
            
            # Get username or use user_id if not found
            username = user_map.get(user_id, user_id)
            # Parse the frontend_msgs JSON
            msg_data = frontend_msgs if frontend_msgs else {}
            msg_type = msg_data.get('type', 'unknown_type')
            msg_value = msg_data.get('value', '')

            if username not in result:
                result[username] = {"conversations": {}}
            if conv_id not in result[username]["conversations"]:
                result[username]["conversations"][conv_id] = {"messages": []}

            result[username]["conversations"][conv_id]["messages"].append({
                "id": msg_id,
                "type": msg_type,
                "value": msg_value,
                "created": msg_created.isoformat() if msg_created else None
            })
            message_count += 1

        cur.close()
        conn.close()

        user_count = len(result)
        conversation_count = sum(len(user_data.get("conversations", {})) for user_data in result.values())

        logger.info(f"Retrieved {message_count} messages across {conversation_count} conversations for {user_count} users")
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving conversation data: {e}")
        raise


def get_user_details(connection_string: str, days: int = 7) -> List[User]:
    """
    Fetch detailed user information for users who registered within the last specified number of days.
    
    Args:
        connection_string: PostgreSQL connection string
        days: Number of days to look back
        
    Returns:
        List of User objects
    """
    try:
        conn = get_db_connection(connection_string)
        cur = conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT 
            id, 
            name, 
            given_name, 
            email, 
            organization
        FROM users
        WHERE created >= %s
        ORDER BY created DESC;
        """
        
        cur.execute(query, (cutoff_date,))
        
        users = []
        for row in cur.fetchall():
            user = User(
                id=row[0],
                name=row[1] or "",
                given_name=row[2] or "",
                email=row[3] or "",
                organization=row[4] or "-"
            )
            users.append(user)
        
        cur.close()
        conn.close()
        
        logger.info(f"Retrieved detailed information for {len(users)} users")
        return users
    
    except Exception as e:
        logger.error(f"Error fetching detailed user information: {e}")
        raise


# ================================================================== #
# Retrieval and Export
# ================================================================== #
def get_data(connection_string: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
    try:
        # Load environment variables if needed
        if not connection_string:
            
            # Build connection string from environment variables
            db_user = os.getenv("PG_USER")
            db_pass = os.getenv("PG_PASS")
            db_host = os.getenv("PG_HOST")
            db_port = os.getenv("PG_PORT")
            db_name = os.getenv("PG_DB")
            
            if not all([db_user, db_pass, db_host, db_port, db_name]):
                raise ValueError("Missing database connection parameters in environment variables")
                
            connection_string = (
                f"postgresql://{db_user}:{db_pass}@{db_host}:"
                f"{db_port}/{db_name}?sslmode=disable"
            )

        user_map = get_new_users(connection_string, days)
        data = get_nested_data(user_map, connection_string)
        detailed_users = get_user_details(connection_string, days)
        
        return data, detailed_users
        
    except Exception as e:
        logger.error(f"Failed to retrieve weekly data: {e}")
        raise


def export_weekly_data(output_file: str = "user_data_export.json", days: int = 7) -> str:
    try:

        data = get_data(days=days)
        
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Data successfully exported to {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Failed to export weekly data: {e}")
        raise


# ================================================================== #
# For testing purposes when run directly
# ================================================================== #
if __name__ == "__main__":
    try:
        # This is just for testing when run directly
        load_dotenv(".chat.env")
        logger.info("Running in standalone mode for testing")
        
        output_file = export_weekly_data()
        logger.info(f"Test export completed: {output_file}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")