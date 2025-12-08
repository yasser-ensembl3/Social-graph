"""
Jina Reader API client for converting URLs to Markdown.

Takes any URL and returns clean, readable Markdown content.
"""
import os
from pathlib import Path
from typing import Optional
import httpx

# Load env
env_file = Path(__file__).parent.parent.parent.parent / ".env.local"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())


class JinaReader:
    """
    Client for Jina Reader API.

    Converts any URL to clean Markdown content.
    """

    BASE_URL = "https://r.jina.ai"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("JINA_API_KEY")

        headers = {
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.Client(
            timeout=60.0,
            headers=headers,
            follow_redirects=True
        )

    def read_url(self, url: str) -> dict:
        """
        Convert a URL to Markdown content.

        Args:
            url: The URL to read

        Returns:
            Dict with title, content (markdown), and metadata
        """
        try:
            # Jina Reader API: GET https://r.jina.ai/{url}
            resp = self.client.get(f"{self.BASE_URL}/{url}")
            resp.raise_for_status()

            data = resp.json()

            return {
                "success": True,
                "url": url,
                "title": data.get("data", {}).get("title", ""),
                "content": data.get("data", {}).get("content", ""),
                "description": data.get("data", {}).get("description", ""),
                "published_date": data.get("data", {}).get("publishedTime"),
                "author": data.get("data", {}).get("author"),
                "word_count": len(data.get("data", {}).get("content", "").split()),
            }

        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "url": url,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            }
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }

    def read_multiple(self, urls: list[str]) -> list[dict]:
        """
        Read multiple URLs.

        Args:
            urls: List of URLs to read

        Returns:
            List of results (some may have failed)
        """
        results = []
        for i, url in enumerate(urls):
            print(f"  [{i+1}/{len(urls)}] Reading: {url[:60]}...")
            result = self.read_url(url)
            results.append(result)

            if result["success"]:
                print(f"    ✓ {result['word_count']} words")
            else:
                print(f"    ✗ {result['error'][:50]}")

        return results

    def close(self):
        self.client.close()


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python jina.py <url>")
        print("Example: python jina.py https://medium.com/@example/article")
        sys.exit(1)

    url = sys.argv[1]

    reader = JinaReader()

    print(f"Reading: {url}\n")

    try:
        result = reader.read_url(url)

        if result["success"]:
            print(f"Title: {result['title']}")
            print(f"Author: {result.get('author', 'N/A')}")
            print(f"Date: {result.get('published_date', 'N/A')}")
            print(f"Word count: {result['word_count']}")
            print(f"\n{'='*60}")
            print("CONTENT (first 2000 chars):")
            print("="*60)
            print(result['content'][:2000])
            if len(result['content']) > 2000:
                print(f"\n... [{len(result['content']) - 2000} more characters]")
        else:
            print(f"Error: {result['error']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        reader.close()
