"""Business logic shared by the MCP tools and the tests."""
from . import publishers, store


def create_post(text: str, platform: str = "dryrun") -> dict:
    publishers.validate(text, platform)
    return store.create(text, platform)


def publish_post(post_id: int) -> dict:
    post = store.get(post_id)
    if not post:
        return {"error": f"No post with id {post_id}"}
    if post["status"] == "published":
        return {"error": "Already published", "post": post}
    try:
        result = publishers.publish(post["text"], post["platform"])
        return store.mark(post_id, "published", result)
    except publishers.PublishError as e:
        return store.mark(post_id, "failed", str(e))


def publish_due() -> list[dict]:
    return [publish_post(p["id"]) for p in store.due()]
