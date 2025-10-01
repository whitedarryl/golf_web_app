import os
import re
from datetime import datetime

def get_latest_course():
    folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pattern = re.compile(
        r'^(.+?)\s+\w+\s+\d{4}\s+Callaway scoring sheet\.xlsx$', re.IGNORECASE
    )

    for filename in os.listdir(folder):
        match = pattern.match(filename)
        if match:
            course_name = match.group(1)

            # ✅ Get today's date
            today = datetime.today()
            formatted_date = today.strftime("%B %d, %Y").replace(" 0", " ")

            return {
                "course_name": course_name,
                "date_played": formatted_date
            }

    return {
        "course_name": "Unknown Course",
        "date_played": datetime.today().strftime("%B %d, %Y").replace(" 0", " ")
    }
