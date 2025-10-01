"""
Centralized course ID management for the Golf Tournament App.

This module provides a single source of truth for the current tournament's course_id.
All apps should use get_current_course_id() instead of hardcoding values.
"""
import os
from typing import Optional
from utils.db import get_db_cursor

def get_current_course_id() -> int:
    """
    Get the current tournament's course_id.

    Priority:
    1. CURRENT_COURSE_ID environment variable (for manual override)
    2. Latest course_id from database (most recent tournament)
    3. Default to 1 if database is empty

    Returns:
        int: The course_id to use for all operations
    """
    # Check environment variable first
    env_course_id = os.getenv('CURRENT_COURSE_ID')
    if env_course_id:
        try:
            return int(env_course_id)
        except ValueError:
            pass

    # Query database for latest course
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(course_id), 1) FROM courses")
            result = cursor.fetchone()
            return result[0] if result else 1
    except Exception as e:
        print(f"⚠️ Warning: Could not get course_id from database: {e}")
        return 1


def set_current_course_id(course_id: int) -> None:
    """
    Set the current course_id in the environment.
    This is useful for testing or manual overrides.

    Args:
        course_id: The course_id to set as current
    """
    os.environ['CURRENT_COURSE_ID'] = str(course_id)


def get_or_create_course(course_name: str, tournament_date: str) -> int:
    """
    Get existing course_id or create a new course entry.

    Args:
        course_name: Name of the golf course
        tournament_date: Date of tournament (YYYY-MM-DD format)

    Returns:
        int: The course_id
    """
    with get_db_cursor() as cursor:
        # Check if course exists
        cursor.execute("""
            SELECT course_id FROM courses
            WHERE course_name = %s AND tournament_date = %s
        """, (course_name, tournament_date))

        result = cursor.fetchone()
        if result:
            return result[0]

        # Create new course
        cursor.execute("""
            INSERT INTO courses (course_name, tournament_date)
            VALUES (%s, %s)
        """, (course_name, tournament_date))

        # Get the inserted ID
        cursor.execute("SELECT LAST_INSERT_ID()")
        return cursor.fetchone()[0]


def clear_course_override() -> None:
    """Remove the CURRENT_COURSE_ID environment variable override."""
    if 'CURRENT_COURSE_ID' in os.environ:
        del os.environ['CURRENT_COURSE_ID']
