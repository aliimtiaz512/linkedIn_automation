import base64
import json
import os
import requests

API_BASE = "https://api.linkedin.com/v2"


def _headers():
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    if not token:
        raise EnvironmentError("LINKEDIN_ACCESS_TOKEN is not set")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def _decode_jwt_sub(token: str) -> str | None:
    """
    Decode the 'sub' (subject = person ID) from a LinkedIn JWT access token.
    No API call or extra scope needed — just base64-decode the payload section.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        # JWT payload is base64url — fix padding then decode
        padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        return str(payload["sub"]) if "sub" in payload else None
    except Exception:
        return None


def get_person_id() -> str:
    """
    Return the LinkedIn member's person ID. Tries three methods in order:

      1. /v2/userinfo  — works when token has 'openid profile' scope (new apps)
      2. JWT decode    — works when access token is a JWT with 'sub' claim
      3. LINKEDIN_PERSON_ID env var — permanent manual fallback
    """
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")

    # ── Method 1: /v2/userinfo (openid + profile scope) ──────────────────────
    try:
        resp = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if resp.status_code == 200:
            person_id = resp.json().get("sub", "")
            if person_id:
                print(f"Person ID from /v2/userinfo: ...{person_id[-6:]}")
                return person_id
        else:
            print(f"userinfo [{resp.status_code}] — trying next method")
    except Exception as e:
        print(f"userinfo error: {e}")

    # ── Method 2: decode JWT token payload ───────────────────────────────────
    person_id = _decode_jwt_sub(token)
    if person_id:
        print(f"Person ID from JWT token: ...{person_id[-6:]}")
        return person_id

    # ── Method 3: explicit env var (set once in GitHub secrets) ──────────────
    person_id = os.environ.get("LINKEDIN_PERSON_ID", "").strip()
    if person_id:
        print("Person ID from LINKEDIN_PERSON_ID secret")
        return person_id

    raise RuntimeError(
        "Cannot determine LinkedIn Person ID.\n"
        "Your token needs 'openid profile' scope. Re-generate it using:\n"
        "https://www.linkedin.com/oauth/v2/authorization?response_type=code"
        "&client_id=YOUR_CLIENT_ID"
        "&redirect_uri=https://oauth.pstmn.io/v1/callback"
        "&scope=openid%20profile%20w_member_social\n"
        "Then run: python scripts/get_linkedin_id.py\n"
        "And add the printed ID as LINKEDIN_PERSON_ID in GitHub secrets."
    )


def _register_image_upload(person_id):
    """Step 1 of image upload: register with LinkedIn and get upload URL + asset URN."""
    payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": f"urn:li:person:{person_id}",
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent",
                }
            ],
        }
    }
    resp = requests.post(
        f"{API_BASE}/assets?action=registerUpload",
        headers=_headers(),
        json=payload,
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Image register failed: {resp.status_code} {resp.text}")
    value = resp.json()["value"]
    upload_url = value["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]
    asset_urn = value["asset"]
    return upload_url, asset_urn


def _upload_image_bytes(upload_url, image_path):
    """Step 2: PUT the image bytes to the pre-signed LinkedIn upload URL."""
    token = os.environ["LINKEDIN_ACCESS_TOKEN"]
    with open(image_path, "rb") as f:
        resp = requests.put(
            upload_url,
            data=f,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Image upload failed: {resp.status_code} {resp.text}")


def post_to_linkedin(content: str, image_path: str = None) -> str:
    """
    Publish a text (+ optional image) post to LinkedIn.
    Returns the post ID string on success.
    """
    person_id = get_person_id()
    author_urn = f"urn:li:person:{person_id}"

    share_content = {
        "shareCommentary": {"text": content},
        "shareMediaCategory": "NONE",
    }

    if image_path:
        try:
            upload_url, asset_urn = _register_image_upload(person_id)
            _upload_image_bytes(upload_url, image_path)
            share_content["shareMediaCategory"] = "IMAGE"
            share_content["media"] = [
                {
                    "status": "READY",
                    "description": {"text": ""},
                    "media": asset_urn,
                    "title": {"text": ""},
                }
            ]
            print("Image uploaded to LinkedIn successfully")
        except Exception as e:
            print(f"Image upload failed ({e}), falling back to text-only post")

    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    resp = requests.post(
        f"{API_BASE}/ugcPosts",
        headers=_headers(),
        json=payload,
        timeout=20,
    )

    if resp.status_code not in (200, 201):
        raise RuntimeError(f"LinkedIn post failed: {resp.status_code} {resp.text}")

    post_id = resp.headers.get("x-restli-id", "unknown")
    print(f"LinkedIn post published! ID: {post_id}")
    return post_id
