import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os
import sys

# Import course manager
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db import get_latest_course_id

def import_handicap_ranks(file_path):
    load_dotenv()
    db_config = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME")
    }

    df = pd.read_csv(file_path)
    required_columns = ["hole_number", "handicap_rank"]
    if not all(col in df.columns for col in required_columns):
        print(f"Error: The CSV file must contain the following columns: {required_columns}")
        return

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Get current course_id dynamically
    course_id = get_latest_course_id()

    # if course:
    #     course_id = course[0]
    #     print(f"Course already exists with ID: {course_id}. Skipping course insertion.")
    # else:
        
    #     cursor.execute("SELECT LAST_INSERT_ID();")
    #     course_id = cursor.fetchone()[0]
    #     print(f"Inserted new course with ID: {course_id}")

    insert_query = """
    INSERT INTO course_hole_handicap (course_id, hole_number, handicap_rank)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE handicap_rank = VALUES(handicap_rank);
    """

    for _, row in df.iterrows():
        values = (course_id, int(row['hole_number']), int(row['handicap_rank']))
        cursor.execute(insert_query, values)

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Handicap ranks imported successfully for course ID: {course_id}")

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
file_path = os.path.join(root_dir, "handicap_ranks.csv")
import_handicap_ranks(file_path)
