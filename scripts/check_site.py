#!/usr/bin/env python3
import os
import requests
import json
import re
from datetime import datetime
from urllib.parse import urlparse, urljoin

# Configuration
TARGET_URL = os.environ.get("TARGET_URL", "https://example.com")
TIMEOUT = int(os.environ.get("TIMEOUT", "10"))
OUT_PATH = os.environ.get("OUT_PATH", "docs/status.json")

# Use a realistic User-Agent to reduce blocking
HEADERS = {
    "User-Agent": os.environ.get(
        "REQUESTS_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/117.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

def get_title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else ""

def parse_tiktok_profile(html, base_url):
    """
    Try to parse TikTok profile HTML and return info about the latest post.
    Strategies:
      1) Look for <script id="SIGI_STATE"> JSON → ItemModule contains videos and stats.
      2) Fallback: regex search for "playCount":<number> in the HTML and take the first.
    Returns a dict with keys: id, link, play_count (int), text (optional).
    """
    # 1) Try SIGI_STATE script tag
    sigi_match = re.search(r'<script[^>]*id=["\']SIGI_STATE["\'][^>]*>(\{.*?\})</script>', html, re.DOTALL)
    if sigi_match:
        try:
            payload = json.loads(sigi_match.group(1))
            item_module = payload.get("ItemModule") or payload.get("ItemList") or {}
            if isinstance(item_module, dict) and item_module:
                # ItemModule keys are video ids; take the first (insertion order usually recent)
                for vid, meta in item_module.items():
                    stats = meta.get("stats") or {}
                    play_count = stats.get("playCount") or stats.get("play_count")
                    try:
                        play_count = int(play_count)
                    except Exception:
                        pc = re.sub(r"[^\d]", "", str(play_count or ""))
                        play_count = int(pc) if pc else None
                    # Build a link if possible
                    video_url = None
                    if "id" in meta:
                        video_url = meta.get("video", {}).get("playAddr") if isinstance(meta.get("video"), dict) else None
                    if not video_url:
                        author = meta.get("author") or meta.get("authorName") or None
                        if author and vid:
                            video_url = urljoin(base_url, f"/video/{vid}")
                    return {
                        "id": vid,
                        "link": video_url,
                        "play_count": play_count,
                        "text": meta.get("desc") or meta.get("description") or None
                    }
        except Exception:
            pass

    # 2) Fallback: look for first numeric "playCount"
    m = re.search(r'"playCount"\s*:\s*"?(?P<count>[\d,]+)"?', html)
    if m:
        pc = int(re.sub(r"[^\d]", "", m.group("count")))
        link_match = re.search(r'(https?://www\.tiktok\.com/@[^/]+/video/\d+)', html)
        link = link_match.group(1) if link_match else None
        return {"id": None, "link": link, "play_count": pc, "text": None}

    # 3) Last-ditch: plain text like "1.2M views"
    text_match = re.search(r'([0-9][\d,.]*\s*(?:views))', html, re.IGNORECASE)
    if text_match:
        num = re.sub(r"[^\d]", "", text_match.group(1))
        try:
            pc = int(num)
        except Exception:
            pc = None
        return {"id": None, "link": None, "play_count": pc, "text": text_match.group(1)}

    return None

def main():
    result = {
        "url": TARGET_URL,
        "checked_at": datetime.utcnow().isoformat() + "Z",
        "ok": False,
        "status_code": None,
        "title": None,
        "latest_post": None,
        "error": None,
    }

    try:
        r = requests.get(TARGET_URL, headers=HEADERS, timeout=TIMEOUT)
        result["status_code"] = r.status_code
        result["title"] = get_title(r.text)
        result["ok"] = r.ok

        parsed = urlparse(TARGET_URL)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        if "tiktok.com" in parsed.netloc.lower():
            # Special handling for TikTok profile pages
            post_info = parse_tiktok_profile(r.text, base_url)
            if post_info:
                result["latest_post"] = post_info
            else:
                result["error"] = "Could not parse latest TikTok post info from HTML."
                result["ok"] = False
        else:
            # Generic site: nothing more than title/status
            pass

    except Exception as e:
        result["error"] = str(e)
        result["ok"] = False

    # Ensure output directory exists (useful when running locally)
    out_dir = os.path.dirname(OUT_PATH) or "."
    os.makedirs(out_dir, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("Wrote", OUT_PATH, ":", result)

if __name__ == "__main__":
    main()
