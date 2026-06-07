"""
Run this ONCE locally to find your LinkedIn Person ID.

Steps:
  1. First regenerate your LinkedIn token WITH r_liteprofile scope (see instructions below)
  2. Paste the new token in your .env as LINKEDIN_ACCESS_TOKEN
  3. Run:  python scripts/get_linkedin_id.py
  4. Copy the printed Person ID
  5. Add it as LINKEDIN_PERSON_ID in GitHub secrets → it never expires

─────────────────────────────────────────────────────────────────────────────
HOW TO GET A TOKEN WITH r_liteprofile SCOPE
─────────────────────────────────────────────────────────────────────────────
Open this URL in your browser (replace YOUR_CLIENT_ID):

  https://www.linkedin.com/oauth/v2/authorization?response_type=code
    &client_id=YOUR_CLIENT_ID
    &redirect_uri=https://oauth.pstmn.io/v1/callback
    &scope=r_liteprofile%20w_member_social

After clicking Allow, you get a ?code=XYZ in the redirect URL.
Exchange it with PowerShell:

  $body = @{
      grant_type    = "authorization_code"
      code          = "PASTE_CODE_HERE"
      redirect_uri  = "https://oauth.pstmn.io/v1/callback"
      client_id     = "YOUR_CLIENT_ID"
      client_secret = "YOUR_CLIENT_SECRET"
  }
  $r = Invoke-RestMethod -Uri "https://www.linkedin.com/oauth/v2/accessToken" `
       -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
  $r.access_token   # ← copy this into .env

─────────────────────────────────────────────────────────────────────────────
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

print("Calling LinkedIn /v2/me ...")
resp = requests.get(
    "https://api.linkedin.com/v2/me",
    headers={
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
    },
    timeout=15,
)

print(f"Status: {resp.status_code}")
print(f"Body  : {resp.text}\n")

if resp.status_code == 200:
    person_id = resp.json().get("id", "")
    print("=" * 60)
    print(f"  Your LinkedIn Person ID:  {person_id}")
    print("=" * 60)
    print()
    print("Add this to GitHub secrets as:  LINKEDIN_PERSON_ID")
    print("It never expires — you only need to do this once.")
else:
    print("ERROR: Could not fetch profile.")
    print("Make sure your token was generated with 'r_liteprofile' scope.")
    print("See the instructions at the top of this file.")
    sys.exit(1)
