#!/usr/bin/env python3
import os
import requests
import json
import re
from datetime import datetime

TARGET_URL = os.environ.get("TARGET_URL", "https://example.com")
TIMEOUT = 10

def get_title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE|re.DOTALL)
    return m.group(1).strip() if m else ""

def main():
    result = {
        "url": TARGET_URL,
        "checked_at": datetime.utcnow().isoformat() + "Z"
    }
    try:
        r = requests.get(TARGET_URL, timeout=TIMEOUT)
        result["status_code"] = r.status_code
        result["title"] = get_title(r.text)
        result["ok"] = r.ok
    except Exception as e:
        result["error"] = str(e)
        result["ok"] = False

    with open("status.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print("Wrote status.json:", result)

if __name__ == "__main__":
    main()
