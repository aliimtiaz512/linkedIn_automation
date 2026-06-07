import tempfile
import urllib.parse
import requests

# Pollinations.ai blocks bare server requests but accepts browser-like User-Agents.
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://pollinations.ai/",
    "Accept-Language": "en-US,en;q=0.9",
}


def _try_download(url: str) -> bytes | None:
    """Try GET on a URL; return image bytes on success, None otherwise."""
    try:
        resp = requests.get(url, headers=_BROWSER_HEADERS, timeout=90)
        if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
            return resp.content
        print(f"      [{resp.status_code}] {url[:80]}")
    except Exception as e:
        print(f"      [ERR] {url[:80]} — {e}")
    return None


def generate_image(prompt: str) -> str:
    """
    Generate an image via Pollinations.ai (free, no API key needed).
    Returns the path to a saved JPEG temp file.

    Tries multiple URL formats in order — Pollinations.ai sometimes 402s
    on certain param combos when called from server IPs, so we fall through.
    """
    encoded = urllib.parse.quote(prompt)
    base = f"https://image.pollinations.ai/prompt/{encoded}"

    attempts = [
        f"{base}?width=1024&height=1024&nologo=true",  # preferred size
        f"{base}?width=800&height=800&nologo=true",     # smaller fallback
        f"{base}?nologo=true",                          # minimal params
        base,                                           # bare URL, no params
    ]

    print(f"Generating image for: {prompt[:70]}...")
    for url in attempts:
        data = _try_download(url)
        if data:
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            tmp.write(data)
            tmp.close()
            print(f"Image saved → {tmp.name} ({len(data) // 1024} KB)")
            return tmp.name

    raise RuntimeError(
        "All Pollinations.ai attempts failed (service may be blocking CI IPs). "
        "Post will be text-only."
    )
