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


def get_person_id():
    """Return the authenticated member's LinkedIn person ID."""
    resp = requests.get(f"{API_BASE}/userinfo", headers=_headers(), timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"Could not fetch profile: {resp.status_code} {resp.text}")
    return resp.json()["sub"]


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
