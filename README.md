# Content Scheduler MCP Server

An MCP (Model Context Protocol) server that lets an AI assistant such as Claude draft, schedule and publish social media posts through a real API (Bluesky), with a safe dry-run mode for testing.

## Tools

| Tool | What it does |
|---|---|
| `create_post(text, platform)` | Save a draft (`dryrun` or `bluesky`), with per-platform length checks |
| `schedule_post(post_id, when_iso)` | Schedule for an ISO 8601 time |
| `list_posts(status)` | View the queue: draft, scheduled, published, failed |
| `publish_now(post_id)` | Publish immediately |
| `publish_due()` | Publish everything whose time has arrived |
| `delete_post(post_id)` | Remove an unpublished post |

## Setup

```bash
pip install -r requirements.txt
python -m unittest discover -s tests      # core logic tests
```

Optional, for real posting: create a Bluesky **app password** (Settings > Privacy and security > App passwords) and set `BLUESKY_HANDLE` and `BLUESKY_APP_PASSWORD` (see `.env.example`). Without them, use `dryrun`.

## Connect to Claude Desktop

Add to `claude_desktop_config.json`, using the full path to this folder:

```json
{
  "mcpServers": {
    "content-scheduler": {
      "command": "python",
      "args": ["-m", "content_scheduler.server"],
      "cwd": "/full/path/to/content-scheduler-mcp",
      "env": {
        "BLUESKY_HANDLE": "yourname.bsky.social",
        "BLUESKY_APP_PASSWORD": "xxxx-xxxx-xxxx-xxxx"
      }
    }
  }
}
```

Restart Claude Desktop, then try: *"Draft three posts about my AI music project, schedule them for tomorrow at 9, 12 and 6 PM IST, and show me the queue."*

## Design

- `store.py`: SQLite queue, no MCP code
- `publishers.py`: platform adapters and validation; add a new platform by adding one function and one limit
- `service.py`: logic shared by the tools and tests
- `server.py`: thin MCP layer built on FastMCP

## Ideas to extend

Add a YouTube or Instagram adapter, an `ai_caption` tool, image or audio attachments, or a scheduler loop that calls `publish_due` every minute.
