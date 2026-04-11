"""Supabase client wrapper for PostGenie."""
import requests
from typing import Optional
from lib.config import SUPABASE_URL, SUPABASE_SERVICE_KEY


class SupabaseClient:
    """Minimal Supabase REST client (no external package needed)."""

    def __init__(self, url: str = SUPABASE_URL, key: str = SUPABASE_SERVICE_KEY):
        self.url = url.rstrip("/") if url else ""
        self.key = key
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.url}/rest/v1/{path}"
        resp = requests.request(method, url, headers=self.headers, **kwargs)
        if not resp.ok:
            raise Exception(f"Supabase error ({resp.status_code}): {resp.text}")
        return resp.json() if resp.content else []

    # ─── Users ───
    def upsert_user(self, email: str, name: str = "", picture: str = "") -> dict:
        """Create or update user by email."""
        existing = self._request("GET", f"pg_users?email=eq.{email}")
        if existing:
            user = existing[0]
            self._request(
                "PATCH",
                f"pg_users?id=eq.{user['id']}",
                json={"name": name, "picture": picture, "updated_at": "now()"},
            )
            return user
        data = self._request(
            "POST",
            "pg_users",
            json={"email": email, "name": name, "picture": picture},
        )
        return data[0] if data else {}

    def get_user_by_email(self, email: str) -> Optional[dict]:
        results = self._request("GET", f"pg_users?email=eq.{email}")
        return results[0] if results else None

    def update_user_plan(self, user_id: str, plan: str, subscription_id: str = ""):
        return self._request(
            "PATCH",
            f"pg_users?id=eq.{user_id}",
            json={"plan": plan, "paddle_subscription_id": subscription_id},
        )

    # ─── Blog Connections ───
    def add_blog_connection(self, user_id: str, platform: str, blog_id: str,
                            blog_name: str = "", refresh_token: str = "",
                            access_token: str = "", **kwargs) -> dict:
        payload = {
            "user_id": user_id,
            "platform": platform,
            "blog_id": blog_id,
            "blog_name": blog_name,
            "refresh_token": refresh_token,
            "access_token": access_token,
            **kwargs,
        }
        data = self._request("POST", "pg_blog_connections", json=payload)
        return data[0] if data else {}

    def get_user_blogs(self, user_id: str) -> list:
        return self._request("GET", f"pg_blog_connections?user_id=eq.{user_id}")

    def delete_blog_connection(self, blog_id: str, user_id: str):
        return self._request(
            "DELETE", f"pg_blog_connections?id=eq.{blog_id}&user_id=eq.{user_id}"
        )

    # ─── Schedules ───
    def create_schedule(self, user_id: str, blog_connection_id: str,
                        name: str, categories: list, language: str = "en",
                        frequency: str = "daily", **kwargs) -> dict:
        payload = {
            "user_id": user_id,
            "blog_connection_id": blog_connection_id,
            "name": name,
            "categories": categories,
            "language": language,
            "frequency": frequency,
            **kwargs,
        }
        data = self._request("POST", "pg_post_schedules", json=payload)
        return data[0] if data else {}

    def get_user_schedules(self, user_id: str) -> list:
        return self._request("GET", f"pg_post_schedules?user_id=eq.{user_id}")

    def get_due_schedules(self) -> list:
        """Get all schedules due to run now (for cron worker)."""
        return self._request(
            "GET",
            "pg_post_schedules?enabled=eq.true&next_run_at=lte.now()",
        )

    def update_schedule_run(self, schedule_id: str, next_run_at: str):
        return self._request(
            "PATCH",
            f"pg_post_schedules?id=eq.{schedule_id}",
            json={"last_run_at": "now()", "next_run_at": next_run_at},
        )

    def toggle_schedule(self, schedule_id: str, enabled: bool):
        return self._request(
            "PATCH",
            f"pg_post_schedules?id=eq.{schedule_id}",
            json={"enabled": enabled},
        )

    def delete_schedule(self, schedule_id: str, user_id: str):
        return self._request(
            "DELETE", f"pg_post_schedules?id=eq.{schedule_id}&user_id=eq.{user_id}"
        )

    # ─── Posts ───
    def create_post(self, schedule_id: str, user_id: str, title: str,
                    content: str, status: str = "pending", **kwargs) -> dict:
        payload = {
            "schedule_id": schedule_id,
            "user_id": user_id,
            "title": title,
            "content": content,
            "status": status,
            **kwargs,
        }
        data = self._request("POST", "pg_posts", json=payload)
        return data[0] if data else {}

    def update_post_published(self, post_id: str, blog_post_id: str,
                              blog_post_url: str):
        return self._request(
            "PATCH",
            f"pg_posts?id=eq.{post_id}",
            json={
                "status": "published",
                "blog_post_id": blog_post_id,
                "blog_post_url": blog_post_url,
                "published_at": "now()",
            },
        )

    def update_post_failed(self, post_id: str, error_message: str):
        return self._request(
            "PATCH",
            f"pg_posts?id=eq.{post_id}",
            json={"status": "failed", "error_message": error_message},
        )

    def get_user_posts(self, user_id: str, limit: int = 50) -> list:
        return self._request(
            "GET",
            f"pg_posts?user_id=eq.{user_id}&order=created_at.desc&limit={limit}",
        )

    # ─── Usage ───
    def increment_usage(self, user_id: str, tokens: int = 0):
        """Increment today's usage counter."""
        from datetime import date
        today = date.today().isoformat()
        existing = self._request(
            "GET", f"pg_usage_daily?user_id=eq.{user_id}&date=eq.{today}"
        )
        if existing:
            row = existing[0]
            return self._request(
                "PATCH",
                f"pg_usage_daily?id=eq.{row['id']}",
                json={
                    "posts_generated": row["posts_generated"] + 1,
                    "tokens_used": row["tokens_used"] + tokens,
                },
            )
        return self._request(
            "POST",
            "pg_usage_daily",
            json={
                "user_id": user_id,
                "date": today,
                "posts_generated": 1,
                "tokens_used": tokens,
            },
        )


# Singleton
db = SupabaseClient()
