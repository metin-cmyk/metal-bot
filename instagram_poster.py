"""Instagram Graph API ile fotoğraf paylaşır."""

import os
import time
import base64
import logging
import requests
from pathlib import Path

log = logging.getLogger(__name__)

IG_USER_ID    = os.environ["IG_USER_ID"]
ACCESS_TOKEN  = os.environ["IG_ACCESS_TOKEN"]
IMGBB_API_KEY = os.environ["IMGBB_API_KEY"]
GRAPH_URL     = "https://graph.instagram.com/v21.0"

def _upload_imgbb(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    r = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": IMGBB_API_KEY, "image": b64, "expiration": 3600},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["data"]["url"]

def post_to_instagram(image_path: Path, caption: str) -> str:
    url = _upload_imgbb(image_path)

    # Container oluştur
    r = requests.post(f"{GRAPH_URL}/{IG_USER_ID}/media", params={
        "image_url": url, "caption": caption, "access_token": ACCESS_TOKEN
    }, timeout=30)
    container_id = r.json()["id"]

    # Hazır olmasını bekle
    for _ in range(12):
        r = requests.get(f"{GRAPH_URL}/{container_id}", params={
            "fields": "status_code", "access_token": ACCESS_TOKEN
        }, timeout=15)
        if r.json().get("status_code") == "FINISHED":
            break
        time.sleep(5)

    # Yayınla
    r = requests.post(f"{GRAPH_URL}/{IG_USER_ID}/media_publish", params={
        "creation_id": container_id, "access_token": ACCESS_TOKEN
    }, timeout=30)
    return r.json()["id"]
