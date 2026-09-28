"""Platform adapters. 'dryrun' is the safe default; 'bluesky' posts for real."""
import os
from datetime import datetime, timezone

import requests

LIMITS = {"dryrun": 1000, "bluesky": 300}


class PublishError(Exception):
    pass


def validate(text: str, platform: str) -> None:
    if platform not in LIMITS:
        raise PublishError(f"Unknown platform '{platform}'. Choose from: {', '.join(LIMITS)}")
    if not text.strip():
        raise PublishError("Post text is empty")
    if len(text) > LIMITS[platform]:
        raise PublishError(f"Text is {len(text)} chars; {platform} allows {LIMITS[platform]}")


def _dryrun(text: str) -> str:
    return f"[dry run] would post: {text[:80]}"


def _bluesky(text: str) -> str:
    handle = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_APP_PASSWORD")
    if not handle or not password:
        raise PublishError("Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD (use an app password)")
    base = "https://bsky.social/xrpc"
    try:
        s = requests.post(
            f"{base}/com.atproto.server.createSession",
            json={"identifier": handle, "password": password},
            timeout=15,
        )
        s.raise_for_status()
        session = s.json()
        r = requests.post(
            f"{base}/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {session['accessJwt']}"},
            json={
                "repo": session["did"],
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": text,
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                },
            },
            timeout=15,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        raise PublishError(f"Bluesky request failed: {e}") from e
    return r.json().get("uri", "posted")


def publish(text: str, platform: str) -> str:
    validate(text, platform)
    return {"dryrun": _dryrun, "bluesky": _bluesky}[platform](text)
