"""
Exa.ai API client for semantic search of founder content.

Searches for blog posts, articles, and podcasts about founders.
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


class ExaClient:
    """
    Client for Exa.ai semantic search API.

    Finds blog posts, articles, and podcasts about founders.
    Excludes LinkedIn content.
    """

    BASE_URL = "https://api.exa.ai"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("EXA_API_KEY")
        if not self.api_key:
            raise ValueError("EXA_API_KEY required")

        self.client = httpx.Client(
            timeout=60.0,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
        )

    def search_founder_content(
        self,
        founder_name: str,
        company_name: Optional[str] = None,
        num_results: int = 10,
        include_contents: bool = False
    ) -> dict:
        """
        Search for content written by or about a founder.

        Args:
            founder_name: Full name of the founder
            company_name: Optional company name for better context
            num_results: Maximum results to return
            include_contents: Whether to fetch full text content

        Returns:
            Dict with search results
        """
        # Build search query
        if company_name:
            query = f"Blog posts or articles written by {founder_name} founder of {company_name}, or interviews and podcasts featuring {founder_name}"
        else:
            query = f"Blog posts or articles written by {founder_name}, or interviews and podcasts featuring {founder_name}"

        payload = {
            "query": query,
            "numResults": num_results,
            "excludeDomains": [
                "linkedin.com",
                "facebook.com",
                "twitter.com",
                "x.com",
                "instagram.com"
            ],
            "type": "auto",
            "useAutoprompt": True
        }

        # Add contents options if requested
        if include_contents:
            payload["contents"] = {
                "text": True
            }

        endpoint = "/search"

        try:
            resp = self.client.post(f"{self.BASE_URL}{endpoint}", json=payload)
            resp.raise_for_status()
            data = resp.json()

            # Process results
            results = []
            for item in data.get("results", []):
                result = {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "published_date": item.get("publishedDate"),
                    "author": item.get("author"),
                    "score": item.get("score"),
                }

                # Categorize by URL/content
                url = item.get("url", "").lower()
                if "podcast" in url or "spotify" in url or "apple.com/podcast" in url:
                    result["category"] = "podcast"
                elif "youtube.com" in url or "youtu.be" in url:
                    result["category"] = "video"
                elif "medium.com" in url or "substack" in url or "blog" in url:
                    result["category"] = "blog"
                else:
                    result["category"] = "article"

                # Add content if fetched
                if include_contents and item.get("text"):
                    result["content"] = item.get("text")

                results.append(result)

            return {
                "query": query,
                "results": results,
                "total_found": len(results),
                "blogs": [r for r in results if r["category"] == "blog"],
                "articles": [r for r in results if r["category"] == "article"],
                "podcasts": [r for r in results if r["category"] == "podcast"],
                "videos": [r for r in results if r["category"] == "video"]
            }

        except httpx.HTTPStatusError as e:
            print(f"Exa API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Exa request error: {e}")
            raise

    def search_with_contents(
        self,
        founder_name: str,
        company_name: Optional[str] = None,
        num_results: int = 10
    ) -> dict:
        """
        Search and fetch full content in one call.

        More expensive but convenient.
        """
        return self.search_founder_content(
            founder_name=founder_name,
            company_name=company_name,
            num_results=num_results,
            include_contents=True
        )

    def close(self):
        self.client.close()


# CLI for testing
if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python exa.py <founder_name> [company_name]")
        print("Example: python exa.py 'Ilyas Bakouch' 'Mila'")
        sys.exit(1)

    founder_name = sys.argv[1]
    company_name = sys.argv[2] if len(sys.argv) > 2 else None

    client = ExaClient()

    print(f"Searching for content about: {founder_name}")
    if company_name:
        print(f"Company: {company_name}")

    try:
        results = client.search_founder_content(
            founder_name=founder_name,
            company_name=company_name,
            num_results=10
        )

        print(f"\nQuery: {results['query']}")
        print(f"\nFound {results['total_found']} results:")
        print(f"  - Blogs: {len(results['blogs'])}")
        print(f"  - Articles: {len(results['articles'])}")
        print(f"  - Podcasts: {len(results['podcasts'])}")
        print(f"  - Videos: {len(results['videos'])}")

        print("\n--- Results ---")
        for r in results['results']:
            print(f"\n[{r['category'].upper()}] {r['title']}")
            print(f"  URL: {r['url']}")
            if r.get('published_date'):
                print(f"  Date: {r['published_date']}")
            if r.get('author'):
                print(f"  Author: {r['author']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()
