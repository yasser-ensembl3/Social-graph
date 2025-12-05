"""
YouTube Data API client for finding video content about a person.
"""
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import httpx

# Load env
env_file = Path(__file__).parent.parent.parent.parent / ".env.local"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())


class YouTubeClient:
    """Client for YouTube Data API v3."""

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY required")

        self.client = httpx.Client(timeout=30.0)

    def search_videos(self, query: str, max_results: int = 25) -> list[dict]:
        """
        Search for videos mentioning a person.

        Args:
            query: Search query (e.g., "Prénom Nom interview")
            max_results: Maximum number of results (default 25, max 50)

        Returns:
            List of video results with metadata
        """
        resp = self.client.get(
            f"{self.BASE_URL}/search",
            params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": min(max_results, 50),
                "order": "relevance",
                "key": self.api_key
            }
        )
        resp.raise_for_status()
        data = resp.json()

        videos = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            videos.append({
                "video_id": item.get("id", {}).get("videoId"),
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "channel_title": snippet.get("channelTitle"),
                "channel_id": snippet.get("channelId"),
                "published_at": snippet.get("publishedAt"),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "url": f"https://www.youtube.com/watch?v={item.get('id', {}).get('videoId')}"
            })

        return videos

    def search_person_content(
        self,
        person_name: str,
        person_context: Optional[str] = None,
        max_results: int = 20,
        use_llm_filter: bool = False,
        min_relevance_score: int = 0
    ) -> dict:
        """
        Search for all types of content about a person.
        Runs multiple searches and optionally filters with LLM.

        Args:
            person_name: Full name of the person
            person_context: Brief description (job, company) for better filtering
            max_results: Max results per search type
            use_llm_filter: Whether to use LLM to verify relevance
            min_relevance_score: Minimum score (0-100) to keep results

        Returns:
            Dict with categorized video results
        """
        # Step 1: Collect raw results from YouTube
        search_queries = [
            f'"{person_name}" interview',
            f'"{person_name}" podcast',
            f'"{person_name}" talk OR keynote OR conference',
            f'"{person_name}"',
        ]

        all_videos = []
        seen_ids = set()

        for query in search_queries:
            try:
                videos = self.search_videos(query, max_results=max_results)
                for video in videos:
                    vid_id = video.get("video_id")
                    if vid_id and vid_id not in seen_ids:
                        seen_ids.add(vid_id)
                        all_videos.append(video)
            except Exception as e:
                print(f"    YouTube search error for '{query}': {e}")

        # Step 2: Filter with LLM if enabled
        if use_llm_filter and all_videos:
            try:
                from scripts.enrich.sources.relevance_filter import RelevanceFilter

                print(f"    Filtering {len(all_videos)} videos with LLM...")
                filter = RelevanceFilter()
                context = person_context or f"Professional content about {person_name}"

                filtered_videos = filter.filter_results(
                    person_name=person_name,
                    person_context=context,
                    results=all_videos,
                    min_relevance_score=min_relevance_score
                )

                print(f"    → {len(filtered_videos)} relevant videos kept")
            except Exception as e:
                print(f"    LLM filter error: {e}, using raw results")
                filtered_videos = all_videos
        else:
            filtered_videos = all_videos

        # Step 3: Organize results by category
        results = {
            "interviews": [],
            "podcasts": [],
            "talks": [],
            "own_content": [],
            "mentions": [],
            "all_videos": filtered_videos,
            "total_found": len(filtered_videos),
            "total_raw": len(all_videos)
        }

        for video in filtered_videos:
            category = video.get("category", "mentions")
            if category == "interview":
                results["interviews"].append(video)
            elif category == "podcast":
                results["podcasts"].append(video)
            elif category == "talk":
                results["talks"].append(video)
            elif category == "own_content":
                results["own_content"].append(video)
            else:
                results["mentions"].append(video)

        return results

    def get_channel_info(self, channel_id: str) -> Optional[dict]:
        """Get channel details by ID."""
        resp = self.client.get(
            f"{self.BASE_URL}/channels",
            params={
                "part": "snippet,statistics",
                "id": channel_id,
                "key": self.api_key
            }
        )
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        if not items:
            return None

        channel = items[0]
        snippet = channel.get("snippet", {})
        stats = channel.get("statistics", {})

        return {
            "channel_id": channel_id,
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "custom_url": snippet.get("customUrl"),
            "published_at": snippet.get("publishedAt"),
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
            "subscriber_count": int(stats.get("subscriberCount", 0)),
            "video_count": int(stats.get("videoCount", 0)),
            "view_count": int(stats.get("viewCount", 0)),
            "url": f"https://www.youtube.com/channel/{channel_id}"
        }

    def get_channel_videos(self, channel_id: str, max_results: int = 25) -> list[dict]:
        """Get recent videos from a channel."""
        resp = self.client.get(
            f"{self.BASE_URL}/search",
            params={
                "part": "snippet",
                "channelId": channel_id,
                "type": "video",
                "order": "date",
                "maxResults": min(max_results, 50),
                "key": self.api_key
            }
        )
        resp.raise_for_status()
        data = resp.json()

        videos = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            videos.append({
                "video_id": item.get("id", {}).get("videoId"),
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "published_at": snippet.get("publishedAt"),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "url": f"https://www.youtube.com/watch?v={item.get('id', {}).get('videoId')}"
            })

        return videos

    def close(self):
        self.client.close()


# Quick test
if __name__ == "__main__":
    client = YouTubeClient()

    # Test search
    print("Searching for content about 'Yoshua Bengio'...")
    results = client.search_person_content("Yoshua Bengio", max_results=5)
    print(f"Total videos found: {results['total_found']}")
    print(f"  - Interviews: {len(results['interviews'])}")
    print(f"  - Podcasts: {len(results['podcasts'])}")
    print(f"  - Talks: {len(results['talks'])}")

    if results['all_videos']:
        print("\nTop 3 videos:")
        for v in results['all_videos'][:3]:
            print(f"  [{v['category']}] {v['title']}")
            print(f"    {v['url']}")

    client.close()
