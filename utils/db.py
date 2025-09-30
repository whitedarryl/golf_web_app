"""
Shared database utilities for golf web app.
Provides connection management and common database operations.
"""
import os
import mysql.connector
from contextlib import contextmanager
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "autocommit": False,
    "pool_name": "golf_pool",
    "pool_size": 5,
    "pool_reset_session": True
}


def get_db_config() -> Dict[str, Any]:
    """Get database configuration from environment variables."""
    return {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME")
    }


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Automatically handles connection cleanup and error handling.

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM players")
            results = cursor.fetchall()
    """
    conn = None
    try:
        config = get_db_config()
        conn = mysql.connector.connect(**config)
        yield conn
    except mysql.connector.Error as err:
        print(f"❌ Database connection error: {err}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()


@contextmanager
def get_db_cursor(commit: bool = False):
    """
    Context manager for database cursor with automatic commit/rollback.

    Args:
        commit: Whether to commit the transaction on success (default: False)

    Usage:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("INSERT INTO players (name) VALUES (%s)", ("John Doe",))
    """
    conn = None
    cursor = None
    try:
        config = get_db_config()
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        yield cursor
        if commit:
            conn.commit()
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def mysql_connection():
    """
    Legacy function for backward compatibility.
    Returns a new database connection.

    Note: Consider using get_db_connection() context manager instead.
    """
    try:
        config = get_db_config()
        connection = mysql.connector.connect(**config)
        print("✅ Database connection successful")
        return connection
    except mysql.connector.Error as err:
        print(f"❌ Database connection error: {err}")
        raise


def get_latest_course_id() -> int:
    """Get the latest course ID from the database."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COALESCE(MAX(course_id), 1) FROM courses")
        result = cursor.fetchone()
        return result[0] if result else 1


def get_course_info(course_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get course information by ID or latest course if no ID provided.

    Args:
        course_id: Optional course ID. If None, gets latest course.

    Returns:
        Dictionary with course_id, course_name, and tournament_date
    """
    with get_db_cursor() as cursor:
        if course_id is None:
            cursor.execute("""
                SELECT course_id, course_name, tournament_date
                FROM courses
                ORDER BY course_id DESC
                LIMIT 1
            """)
        else:
            cursor.execute("""
                SELECT course_id, course_name, tournament_date
                FROM courses
                WHERE course_id = %s
            """, (course_id,))

        result = cursor.fetchone()
        if result:
            return {
                "course_id": result[0],
                "course_name": result[1],
                "tournament_date": result[2]
            }
        return {"course_id": 1, "course_name": "Unknown", "tournament_date": None}


def get_player_counts(course_id: Optional[int] = None) -> Dict[str, int]:
    """
    Get player count statistics for a course.

    Args:
        course_id: Optional course ID. If None, uses latest course.

    Returns:
        Dictionary with total_count, submitted_count, and players_left
    """
    if course_id is None:
        course_id = get_latest_course_id()

    with get_db_cursor() as cursor:
        # Get total players
        cursor.execute(
            "SELECT COUNT(*) FROM players WHERE course_id = %s",
            (course_id,)
        )
        total_count = cursor.fetchone()[0]

        # Get submitted scores
        cursor.execute(
            "SELECT COUNT(*) FROM scores WHERE total IS NOT NULL AND course_id = %s",
            (course_id,)
        )
        submitted_count = cursor.fetchone()[0]

        return {
            "total_count": total_count,
            "submitted_count": submitted_count,
            "players_left": max(total_count - submitted_count, 0)
        }


def check_player_exists(first_name: str, last_name: str, course_id: int) -> bool:
    """Check if a player exists for a given course."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT 1 FROM scores
            WHERE course_id = %s AND first_name = %s AND last_name = %s
            LIMIT 1
        """, (course_id, first_name, last_name))
        return cursor.fetchone() is not None


def insert_or_update_score(first_name: str, last_name: str, course_id: int,
                           holes: list, total: int, net_score: int) -> bool:
    """
    Insert or update a player's score.

    Args:
        first_name: Player's first name
        last_name: Player's last name
        course_id: Course ID
        holes: List of 18 hole scores
        total: Total gross score
        net_score: Net score after handicap

    Returns:
        True if successful, False otherwise
    """
    if len(holes) != 18:
        raise ValueError("Must provide exactly 18 hole scores")

    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if player exists
            cursor.execute("""
                SELECT 1 FROM scores
                WHERE first_name = %s AND last_name = %s AND course_id = %s
            """, (first_name, last_name, course_id))

            if cursor.fetchone():
                # Update existing score
                cursor.execute("""
                    UPDATE scores
                    SET hole_1=%s, hole_2=%s, hole_3=%s, hole_4=%s, hole_5=%s,
                        hole_6=%s, hole_7=%s, hole_8=%s, hole_9=%s,
                        hole_10=%s, hole_11=%s, hole_12=%s, hole_13=%s, hole_14=%s,
                        hole_15=%s, hole_16=%s, hole_17=%s, hole_18=%s,
                        total=%s, net_score=%s
                    WHERE first_name=%s AND last_name=%s AND course_id=%s
                """, (*holes, total, net_score, first_name, last_name, course_id))
            else:
                # Insert new score
                cursor.execute("""
                    INSERT INTO scores (
                        first_name, last_name, course_id,
                        hole_1, hole_2, hole_3, hole_4, hole_5, hole_6, hole_7, hole_8, hole_9,
                        hole_10, hole_11, hole_12, hole_13, hole_14, hole_15, hole_16, hole_17, hole_18,
                        total, net_score
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (first_name, last_name, course_id, *holes, total, net_score))

        return True
    except Exception as e:
        print(f"❌ Error inserting/updating score: {e}")
        return False