"""
Run this ONCE locally to find and save your LinkedIn Person ID.

─────────────────────────────────────────────────────────────────────────────
STEP 1 — Get a token with the correct scopes
─────────────────────────────────────────────────────────────────────────────
Open this URL in your browser (replace YOUR_CLIENT_ID):

  https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=https://oauth.pstmn.io/v1/callback&scope=openid%20profile%20w_member_social

Click Allow → browser redirects to a blank page.
Copy the 'code' value from the address bar URL.

─────────────────────────────────────────────────────────────────────────────
STEP 2 — Exchange code for access token (run in PowerShell)
─────────────────────────────────────────────────────────────────────────────
  $body = @{
      grant_type    = "authorization_code"
      code          = "PASTE_CODE_HERE"
      redirect_uri  = "https://oauth.pstmn.io/v1/callback"
      client_id     = "YOUR_CLIENT_ID"
      client_secret = "YOUR_CLIENT_SECRET"
  }
  $r = Invoke-RestMethod -Uri "https://www.linkedin.com/oauth/v2/accessToken" `
       -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
  $r.access_token

─────────────────────────────────────────────────────────────────────────────
STEP 3 — Paste the token into .env then run this script
─────────────────────────────────────────────────────────────────────────────
  python scripts/get_linkedin_id.py

─────────────────────────────────────────────────────────────────────────────
STEP 4 — Add both values to GitHub secrets
─────────────────────────────────────────────────────────────────────────────
  LINKEDIN_ACCESS_TOKEN  →  the token from Step 2 (update every 60 days)
  LINKEDIN_PERSON_ID     →  the ID printed below (permanent, never expires)
"""

import os
import sys

from dotenv import load_dotenv
import requests

load_dotenv()

token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()
if not token:
    print("ERROR: LINKEDIN_ACCESS_TOKEN not set in .env")
    sys.exit(1)

print("Calling LinkedIn /v2/userinfo ...")
resp = requests.get(
    "https://api.linkedin.com/v2/userinfo",
    headers={"Authorization": f"Bearer {token}"},
    timeout=15,
)

print(f"Status: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    person_id = data.get("sub", "")
    name = data.get("name", "")
    print()
    print("=" * 60)
    print(f"  Name            : {name}")
    print(f"  LinkedIn Person ID : {person_id}")
    print("=" * 60)
    print()
    print("Add LINKEDIN_PERSON_ID to GitHub secrets — it never expires.")
    print("Also update LINKEDIN_ACCESS_TOKEN with the new token.")
else:
    print(f"Response: {resp.text}")
    print()
    print("ERROR: Token doesn't have 'openid profile' scope.")
    print("Re-generate the token using the URL in STEP 1 above.")
    sys.exit(1)
