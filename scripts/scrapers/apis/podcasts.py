"""
Listen Notes API client for finding podcast appearances.
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


class ListenNotesClient:
    """
    Client for Listen Notes API - the best podcast search engine.

    Setup:
    1. Get free API key at https://www.listennotes.com/api/
    2. Free tier: 300 requests/month
    """

    BASE_URL = "https://listen-api.listennotes.com/api/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("LISTENNOTES_API_KEY")
        if not self.api_key:
            raise ValueError("LISTENNOTES_API_KEY required")

        self.client = httpx.Client(
            headers={"X-ListenAPI-Key": self.api_key},
            timeout=30.0
        )

    def search_episodes(self, query: str, max_results: int = 10, sort_by: str = "relevance") -> list[dict]:
        """
        Search for podcast episodes.

        Args:
            query: Search query (person name, topic, etc.)
            max_results: Number of results to return
            sort_by: "relevance" or "recent"

        Returns:
            List of episode results
        """
        resp = self.client.get(
            f"{self.BASE_URL}/search",
            params={
                "q": query,
                "type": "episode",
                "sort_by_date": 1 if sort_by == "recent" else 0,
                "len_min": 5,  # Minimum 5 minutes (filter out short clips)
                "only_in": "title,description",
                "page_size": min(max_results, 10)
            }
        )
        resp.raise_for_status()
        data = resp.json()

        episodes = []
        for item in data.get("results", []):
            episodes.append({
                "episode_id": item.get("id"),
                "title": item.get("title_original"),
                "description": item.get("description_original", "")[:500],
                "podcast_name": item.get("podcast", {}).get("title_original"),
                "podcast_id": item.get("podcast", {}).get("id"),
                "publisher": item.get("podcast", {}).get("publisher_original"),
                "audio_url": item.get("audio"),
                "listennotes_url": item.get("listennotes_url"),
                "published_date": item.get("pub_date_ms"),
                "duration_seconds": item.get("audio_length_sec"),
                "thumbnail": item.get("thumbnail"),
                "explicit": item.get("explicit_content", False)
            })

        return episodes

    def search_person_appearances(self, person_name: str, max_results: int = 20) -> dict:
        """
        Search for all podcast appearances of a person.

        Args:
            person_name: Full name of the person
            max_results: Maximum total results

        Returns:
            Dict with categorized podcast results
        """
        results = {
            "episodes": [],
            "as_guest": [],
            "as_host": [],
            "mentioned": [],
            "total_found": 0,
            "podcasts_appeared_on": set()
        }

        # Search with exact name match
        try:
            episodes = self.search_episodes(f'"{person_name}"', max_results=max_results)

            for ep in episodes:
                title = (ep.get("title") or "").lower()
                description = (ep.get("description") or "").lower()
                name_lower = person_name.lower()

                # Categorize the appearance
                if name_lower in title:
                    # Name in title = likely guest or main topic
                    if any(word in title for word in ["interview", "guest", "with", "featuring"]):
                        ep["appearance_type"] = "guest"
                        results["as_guest"].append(ep)
                    elif any(word in title for word in ["host", "presents", "show"]):
                        ep["appearance_type"] = "host"
                        results["as_host"].append(ep)
                    else:
                        ep["appearance_type"] = "featured"
                        results["as_guest"].append(ep)
                else:
                    # Name only in description = mentioned
                    ep["appearance_type"] = "mentioned"
                    results["mentioned"].append(ep)

                results["episodes"].append(ep)

                # Track unique podcasts
                if ep.get("podcast_name"):
                    results["podcasts_appeared_on"].add(ep["podcast_name"])

        except Exception as e:
            print(f"  Listen Notes search error: {e}")

        results["total_found"] = len(results["episodes"])
        results["podcasts_appeared_on"] = list(results["podcasts_appeared_on"])

        return results

    def get_episode_details(self, episode_id: str) -> Optional[dict]:
        """Get detailed info about a specific episode."""
        resp = self.client.get(f"{self.BASE_URL}/episodes/{episode_id}")
        resp.raise_for_status()
        return resp.json()

    def get_podcast_info(self, podcast_id: str) -> Optional[dict]:
        """Get info about a podcast show."""
        resp = self.client.get(f"{self.BASE_URL}/podcasts/{podcast_id}")
        resp.raise_for_status()
        data = resp.json()

        return {
            "podcast_id": data.get("id"),
            "title": data.get("title"),
            "description": data.get("description"),
            "publisher": data.get("publisher"),
            "website": data.get("website"),
            "language": data.get("language"),
            "country": data.get("country"),
            "total_episodes": data.get("total_episodes"),
            "listen_score": data.get("listen_score"),  # Popularity score 0-100
            "listen_score_global_rank": data.get("listen_score_global_rank"),
            "thumbnail": data.get("thumbnail"),
            "listennotes_url": data.get("listennotes_url")
        }

    def close(self):
        self.client.close()


class PodcastIndexClient:
    """
    Alternative: Podcast Index API (completely free, open source).

    Setup:
    1. Get free API key at https://api.podcastindex.org/
    2. Unlimited requests
    """

    BASE_URL = "https://api.podcastindex.org/api/1.0"

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key or os.environ.get("PODCASTINDEX_API_KEY")
        self.api_secret = api_secret or os.environ.get("PODCASTINDEX_API_SECRET")

        if not self.api_key or not self.api_secret:
            raise ValueError("PODCASTINDEX_API_KEY and PODCASTINDEX_API_SECRET required")

        import hashlib
        import time

        # Podcast Index requires auth headers
        epoch_time = str(int(time.time()))
        auth_string = self.api_key + self.api_secret + epoch_time
        auth_hash = hashlib.sha1(auth_string.encode()).hexdigest()

        self.client = httpx.Client(
            headers={
                "User-Agent": "founders-graph/1.0",
                "X-Auth-Key": self.api_key,
                "X-Auth-Date": epoch_time,
                "Authorization": auth_hash
            },
            timeout=30.0
        )

    def search_episodes(self, query: str, max_results: int = 10) -> list[dict]:
        """Search for podcast episodes by person name."""
        resp = self.client.get(
            f"{self.BASE_URL}/search/byterm",
            params={"q": query, "max": max_results}
        )
        resp.raise_for_status()
        data = resp.json()

        episodes = []
        for item in data.get("feeds", []):
            episodes.append({
                "podcast_id": item.get("id"),
                "title": item.get("title"),
                "description": item.get("description"),
                "url": item.get("url"),
                "website": item.get("link"),
                "language": item.get("language"),
                "categories": item.get("categories", {})
            })

        return episodes

    def close(self):
        self.client.close()


# Quick test
if __name__ == "__main__":
    # Test Listen Notes
    try:
        client = ListenNotesClient()
        print("Searching for podcast appearances of 'Yoshua Bengio'...")
        results = client.search_person_appearances("Yoshua Bengio", max_results=10)
        print(f"Total episodes found: {results['total_found']}")
        print(f"  - As guest: {len(results['as_guest'])}")
        print(f"  - Mentioned: {len(results['mentioned'])}")
        print(f"Podcasts appeared on: {results['podcasts_appeared_on']}")

        if results['episodes']:
            print("\nTop 3 episodes:")
            for ep in results['episodes'][:3]:
                print(f"  [{ep.get('appearance_type')}] {ep['title']}")
                print(f"    Podcast: {ep['podcast_name']}")
                print(f"    URL: {ep['listennotes_url']}")

        client.close()
    except ValueError as e:
        print(f"Listen Notes not configured: {e}")
