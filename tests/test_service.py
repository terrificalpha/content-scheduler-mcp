import os
import tempfile
import unittest

os.environ["CONTENT_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

from content_scheduler import service, store  # noqa: E402


class ServiceTests(unittest.TestCase):
    def test_draft_schedule_publish(self):
        p = service.create_post("Hello from my MCP server")
        self.assertEqual(p["status"], "draft")
        s = store.schedule(p["id"], "2000-01-01T00:00:00Z")
        self.assertEqual(s["status"], "scheduled")
        done = service.publish_due()
        self.assertEqual(done[0]["status"], "published")
        self.assertIn("dry run", done[0]["result"])

    def test_future_post_not_published(self):
        p = service.create_post("Later")
        store.schedule(p["id"], "2999-01-01T00:00:00Z")
        self.assertEqual(service.publish_due(), [])

    def test_length_limit(self):
        with self.assertRaises(Exception):
            service.create_post("x" * 301, "bluesky")

    def test_bluesky_without_credentials_fails_cleanly(self):
        for k in ("BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD"):
            os.environ.pop(k, None)
        p = service.create_post("hi", "bluesky")
        r = service.publish_post(p["id"])
        self.assertEqual(r["status"], "failed")

    def test_cannot_delete_published(self):
        p = service.create_post("done")
        service.publish_post(p["id"])
        self.assertFalse(store.delete(p["id"]))


if __name__ == "__main__":
    unittest.main()
