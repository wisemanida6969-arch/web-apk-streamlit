"""Blog publishers for Blogger, WordPress, etc."""
import requests
import base64

from lib.config import BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET


def refresh_google_access_token(refresh_token: str) -> str:
    """Get a new access token using the refresh token."""
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": BLOGGER_CLIENT_ID,
            "client_secret": BLOGGER_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def publish_to_blogger(blog_id: str, title: str, content: str,
                       refresh_token: str, labels: list = None) -> dict:
    """Publish a post to Google Blogger."""
    access_token = refresh_google_access_token(refresh_token)

    resp = requests.post(
        f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "kind": "blogger#post",
            "blog": {"id": blog_id},
            "title": title,
            "content": content,
            "labels": labels or [],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "blog_post_id": data.get("id"),
        "blog_post_url": data.get("url"),
    }


def publish_to_wordpress(site_url: str, username: str, app_password: str,
                         title: str, content: str,
                         categories: list = None, tags: list = None) -> dict:
    """Publish a post to self-hosted WordPress using Application Passwords."""
    site_url = site_url.rstrip("/")
    credentials = base64.b64encode(f"{username}:{app_password}".encode()).decode()

    resp = requests.post(
        f"{site_url}/wp-json/wp/v2/posts",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        },
        json={
            "title": title,
            "content": content,
            "status": "publish",
            "categories": categories or [],
            "tags": tags or [],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "blog_post_id": str(data.get("id", "")),
        "blog_post_url": data.get("link", ""),
    }


def publish_post(blog_connection: dict, title: str, content: str,
                 labels: list = None) -> dict:
    """Dispatch publish call based on platform."""
    platform = blog_connection["platform"]

    if platform == "blogger":
        return publish_to_blogger(
            blog_id=blog_connection["blog_id"],
            title=title,
            content=content,
            refresh_token=blog_connection["refresh_token"],
            labels=labels,
        )
    elif platform == "wordpress":
        return publish_to_wordpress(
            site_url=blog_connection["wp_site_url"],
            username=blog_connection["wp_username"],
            app_password=blog_connection["wp_app_password"],
            title=title,
            content=content,
            tags=labels,
        )
    else:
        raise ValueError(f"Unsupported platform: {platform}")
