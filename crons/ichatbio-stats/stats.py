from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import logging
import os
import psycopg2
from typing import Dict, Any


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


def get_new_users(db, period: Dict[str, datetime]) -> Dict[str, str]:
    """
    Fetch users who registered within the last specified number of days.
    Args:
        db: database cursor to execute queries
        period: {start_date, end_date}
    Returns:
        Array of user objects
    """
    try:

        query = """
        SELECT 
            u.id AS user_id, 
            u.email AS user_email,
            u.given_name AS username,
            u.organization AS organization
        FROM 
            users u
        WHERE 
            u.created >= %s 
            AND u.created < %s
        ORDER BY 
            u.created DESC;
        """
        db.execute(query, (period["start_date"], period["end_date"]))

        users = []
        for row in db.fetchall():
            user_id, user_email, username, organization = row
            # Use username if available, otherwise email
            display_name = username if username else user_email
            users.append({
                "user_id": user_id,
                "username": display_name,
                "user_email": user_email,
                "organization": organization
            })

        return users

    except Exception as e:
        logger.error(f"Error fetching new users: {e}")
        raise


def get_conversations(db, period: Dict[str, datetime]) -> Dict[str, Any]:
    """
    Args:
        db: database cursor to execute queries
        period: {start_date, end_date}
    Returns:
        Array of conversation objects sorted by last_message_created
    """
    try:
        db.execute("SELECT DISTINCT type FROM messages;")
        message_types = [row[0] for row in db.fetchall()]
        # dynamic query to retrieve all message type count
        query = """
        SELECT 
            c.user_id,
            u.given_name,
            c.id AS conversation_id,
            COUNT(m.id) AS total_messages_count
        """
        for type in message_types:
            query += f", COUNT(CASE WHEN m.type = '{type}' THEN 1 END)AS {type}_count"
        query += """,
            MAX(m.created) AS last_message_created
        FROM 
            conversations c
        JOIN users u
            ON u.id = c.user_id
        LEFT JOIN messages m 
            ON c.id = m.conversation_id
        WHERE
            c.created >= %s
            AND c.created < %s
        GROUP BY 
            c.id, c.user_id, u.given_name
        ORDER BY
            MAX(c.created) DESC;
        """

        db.execute(query, (period["start_date"],period["end_date"]))

        conversations = []
        for row in db.fetchall():
            conversation = {
                "user_id": row[0],
                "username": row[1],
                "conv_id": row[2],
                "total_message_count": row[3],
                "last_message_created": row[-1]
            }
            counts = {}
            for i in range(len(message_types)):
                counts[message_types[i]] = row[i + 3]
            conversation["counts"] = counts
            conversations.append(conversation)
        return conversations
        
    except Exception as e:
        logger.error(f"Error retrieving conversation data: {e}")
        raise


# ================================================================== #
# Retrieval and Export
# ================================================================== #
def get_data(days: int = 7) -> Dict[str, Any]:
    try:
        db_user = os.getenv("PG_USER")
        db_pass = os.getenv("PG_PASS")
        db_host = os.getenv("PG_HOST")
        db_port = os.getenv("PG_PORT")
        db_name = os.getenv("PG_DB")
        
        if not all([db_user, db_pass, db_host, db_port, db_name]):
            raise ValueError("Missing database connection parameters in environment variables")

        period = {
            "start_date": datetime.now().date() - timedelta(days=days),
            "end_date": datetime.now().date()
        }

        connection_string = (
            f"postgresql://{db_user}:{db_pass}@{db_host}:"
            f"{db_port}/{db_name}?sslmode=disable"
        )
        conn = get_db_connection(connection_string)
        db = conn.cursor()

        new_users = get_new_users(db, period)
        conversations = get_conversations(db, period)

        db.close()
        conn.close()

        return conversations, new_users
    except Exception as e:
        logger.error(f"Failed to retrieve data: {e}")
        raise


# ================================================================== #
# Test/Export data into JSON
# ================================================================== #
def export_weekly_data(output_file: str = "user_data_export.json") -> str:
    try:
        days = 3
        conversations, users = get_data(days)
        data = {
            "conversations": conversations,
            "new_users": users
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
            
        logger.info(f"Data successfully exported to {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Failed to export weekly data: {e}")
        raise


if __name__ == "__main__":
    try:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()]
        )
        logger = logging.getLogger(__name__)

        load_dotenv(".chat.env")
        logger.info("Running in standalone mode for testing")
        
        output_file = export_weekly_data()
        logger.info(f"Test export completed: {output_file}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
