import json
import os
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Your sheet columns (row 1 headers already set by you):
# A: Content Idea | B: Content | C: Hashtags | D: Log timestamp


def _get_client():
    raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if not raw:
        raise EnvironmentError("GOOGLE_SHEETS_CREDENTIALS is not set")
    creds_dict = json.loads(raw)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def log_to_sheets(sheet_id: str, selected_idea: dict, content: str, hashtags: str, post_id: str = None):
    """
    Append one row to your LinkedIn-Automation Google Sheet.

    Column mapping:
        A  →  Content Idea   (the selected idea title)
        B  →  Content        (post body text)
        C  →  Hashtags       (space-separated hashtags)
        D  →  Log timestamp  (YYYY-MM-DD HH:MM:SS PKT)
    """
    client = _get_client()
    spreadsheet = client.open_by_key(sheet_id)

    # Use the first (and only) worksheet — whatever tab name you gave it
    worksheet = spreadsheet.get_worksheet(0)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [
        selected_idea["title"],  # A — Content Idea
        content,                  # B — Content
        hashtags,                 # C — Hashtags
        timestamp,                # D — Log timestamp
    ]

    worksheet.append_row(row, value_input_option="USER_ENTERED")
    print(f"Google Sheets updated — row appended at {timestamp}")
