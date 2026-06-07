import hashlib
import os
import tempfile
import urllib.parse
import requests

# ── Layer 1: Pollinations.ai (free but blocks many CI IPs) ──────────────────

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://pollinations.ai/",
}


def _pollinations(prompt: str) -> bytes | None:
    encoded = urllib.parse.quote(prompt)
    base = f"https://image.pollinations.ai/prompt/{encoded}"
    for url in [f"{base}?width=1024&height=1024&nologo=true", base]:
        try:
            r = requests.get(url, headers=_BROWSER_HEADERS, timeout=60)
            if r.status_code == 200 and "image" in r.headers.get("Content-Type", ""):
                return r.content
            print(f"      Pollinations [{r.status_code}]")
        except Exception as e:
            print(f"      Pollinations error: {e}")
    return None


# ── Layer 2: Hugging Face Inference API (free account needed → HF_TOKEN) ────
# Sign up free at https://huggingface.co → Settings → Access Tokens → New token
# Add HF_TOKEN to GitHub secrets. Skip this layer if token not set.

_HF_MODEL = "black-forest-labs/FLUX.1-schnell"


def _huggingface(prompt: str) -> bytes | None:
    hf_token = os.environ.get("HF_TOKEN", "").strip()
    if not hf_token:
        return None  # layer not configured — skip silently
    try:
        url = f"https://api-inference.huggingface.co/models/{_HF_MODEL}"
        headers = {"Authorization": f"Bearer {hf_token}"}
        r = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=120)
        if r.status_code == 200 and "image" in r.headers.get("Content-Type", ""):
            print("      Hugging Face image generated ✓")
            return r.content
        print(f"      Hugging Face [{r.status_code}]: {r.text[:120]}")
    except Exception as e:
        print(f"      Hugging Face error: {e}")
    return None


# ── Layer 3: Picsum Photos (guaranteed — no key, always returns an image) ───
# Beautiful high-quality stock photos. Seed is derived from the prompt text
# so the same topic always gets the same photo (consistent per post topic).

def _picsum(prompt: str) -> bytes | None:
    seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16) % 1000
    url = f"https://picsum.photos/seed/{seed}/1200/627"
    try:
        r = requests.get(url, timeout=30, allow_redirects=True)
        if r.status_code == 200 and "image" in r.headers.get("Content-Type", ""):
            print("      Picsum fallback image used ✓")
            return r.content
        print(f"      Picsum [{r.status_code}]")
    except Exception as e:
        print(f"      Picsum error: {e}")
    return None


# ── Public entry point ────────────────────────────────────────────────────────

def generate_image(prompt: str) -> str:
    """
    Generate an image for the LinkedIn post.
    Tries three sources in order — always succeeds unless network is down.

      1. Pollinations.ai   — AI-generated, free (may block CI IPs)
      2. Hugging Face      — AI-generated, free with HF_TOKEN secret
      3. Picsum Photos     — stock photo, always free, no key needed

    Returns the path to a temporary JPEG file.
    """
    print(f"Generating image for: {prompt[:70]}...")

    for label, fn in [
        ("Pollinations.ai", _pollinations),
        ("Hugging Face",    _huggingface),
        ("Picsum Photos",   _picsum),
    ]:
        data = fn(prompt)
        if data:
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            tmp.write(data)
            tmp.close()
            print(f"      [{label}] Image saved → {tmp.name} ({len(data) // 1024} KB)")
            return tmp.name

    raise RuntimeError("All image sources failed. Check network connectivity.")
