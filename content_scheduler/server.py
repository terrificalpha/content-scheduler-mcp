"""MCP server: lets an AI assistant draft, schedule and publish social posts."""
from mcp.server.fastmcp import FastMCP

from . import service, store

mcp = FastMCP("content-scheduler")


@mcp.tool()
def create_post(text: str, platform: str = "dryrun") -> dict:
    """Save a draft post. platform is 'dryrun' (safe test mode) or 'bluesky'."""
    try:
        return service.create_post(text, platform)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def schedule_post(post_id: int, when_iso: str) -> dict:
    """Schedule a post for an ISO 8601 time, e.g. 2026-10-01T09:00:00+05:30."""
    try:
        post = store.schedule(post_id, when_iso)
    except ValueError:
        return {"error": "when_iso must be an ISO 8601 datetime"}
    return post or {"error": f"No post with id {post_id}"}


@mcp.tool()
def list_posts(status: str | None = None) -> list[dict]:
    """List posts, optionally filtered by status: draft, scheduled, published, failed."""
    return store.list_posts(status)


@mcp.tool()
def publish_now(post_id: int) -> dict:
    """Publish a post immediately."""
    return service.publish_post(post_id)


@mcp.tool()
def publish_due() -> list[dict]:
    """Publish every scheduled post whose time has arrived. Call this on a timer or on request."""
    return service.publish_due()


@mcp.tool()
def delete_post(post_id: int) -> dict:
    """Delete an unpublished post."""
    return {"deleted": store.delete(post_id)}


if __name__ == "__main__":
    mcp.run()
