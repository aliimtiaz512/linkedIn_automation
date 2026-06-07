import os
import tempfile
import urllib.parse
import requests

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"


def generate_image(prompt: str) -> str:
    """
    Generate an image via Pollinations.ai (free, no API key needed).
    Returns the path to a temporary JPEG file.
    """
    encoded = urllib.parse.quote(prompt)
    url = POLLINATIONS_URL.format(prompt=encoded)
    # No model param = Pollinations.ai default free model (flux is paid)
    params = {
        "width": 1024,
        "height": 1024,
        "nologo": "true",
    }

    print(f"Generating image for: {prompt[:60]}...")
    resp = requests.get(url, params=params, timeout=90)

    if resp.status_code != 200:
        raise RuntimeError(f"Pollinations.ai returned {resp.status_code}")

    content_type = resp.headers.get("Content-Type", "")
    if "image" not in content_type:
        raise RuntimeError(f"Unexpected content type: {content_type}")

    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.write(resp.content)
    tmp.close()
    print(f"Image saved to: {tmp.name} ({len(resp.content) // 1024} KB)")
    return tmp.name
