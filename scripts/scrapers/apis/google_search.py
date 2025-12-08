"""
Google Custom Search API client for finding web content about a person.
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


class GoogleSearchClient:
    """
    Client for Google Custom Search API.

    Setup required:
    1. Create a Custom Search Engine at https://programmablesearchengine.google.com/
    2. Get API key from https://console.cloud.google.com/apis/credentials
    3. Enable "Search the entire web" in your Custom Search Engine settings
    """

    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.search_engine_id = search_engine_id or os.environ.get("GOOGLE_SEARCH_ENGINE_ID")

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY required")
        if not self.search_engine_id:
            raise ValueError("GOOGLE_SEARCH_ENGINE_ID required")

        self.client = httpx.Client(timeout=30.0)

    def search(self, query: str, num_results: int = 10, start: int = 1) -> list[dict]:
        """
        Perform a Google search.

        Args:
            query: Search query
            num_results: Number of results (max 10 per request)
            start: Start index for pagination (1-based)

        Returns:
            List of search results
        """
        resp = self.client.get(
            self.BASE_URL,
            params={
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": min(num_results, 10),
                "start": start
            }
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("items", []):
            results.append({
                "title": item.get("title"),
                "url": item.get("link"),
                "snippet": item.get("snippet"),
                "display_url": item.get("displayLink"),
                "source": item.get("displayLink", "").replace("www.", "").split("/")[0]
            })

        return results

    def search_person_content(self, person_name: str, max_results_per_category: int = 10) -> dict:
        """
        Search for various types of content about a person.

        Args:
            person_name: Full name of the person
            max_results_per_category: Max results per content type

        Returns:
            Dict with categorized search results
        """
        search_queries = [
            (f'"{person_name}" podcast episode', "podcasts"),
            (f'"{person_name}" interview', "interviews"),
            (f'"{person_name}" conference talk OR keynote', "talks"),
            (f'"{person_name}" article OR blog', "articles"),
            (f'"{person_name}" site:medium.com OR site:substack.com', "blogs"),
            (f'"{person_name}" site:techcrunch.com OR site:forbes.com OR site:bloomberg.com', "press"),
        ]

        results = {
            "podcasts": [],
            "interviews": [],
            "talks": [],
            "articles": [],
            "blogs": [],
            "press": [],
            "all_results": [],
            "total_found": 0
        }

        seen_urls = set()

        for query, category in search_queries:
            try:
                search_results = self.search(query, num_results=max_results_per_category)
                for result in search_results:
                    url = result.get("url")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        results[category].append(result)
                        results["all_results"].append({**result, "category": category})
            except Exception as e:
                print(f"  Google search error for '{query}': {e}")

        results["total_found"] = len(seen_urls)
        return results

    def search_media_appearances(
        self,
        person_name: str,
        company_name: Optional[str] = None,
        use_llm_filter: bool = False,
        min_relevance_score: int = 0
    ) -> dict:
        """
        Specifically search for media appearances (podcasts, videos, interviews).

        Args:
            person_name: Full name of the person
            company_name: Optional company name for more targeted search
            use_llm_filter: Whether to use LLM to verify relevance
            min_relevance_score: Minimum score (0-100) to keep results

        Returns:
            Dict with media appearance results
        """
        # Build search queries
        base_name = f'"{person_name}"'
        if company_name:
            base_name = f'"{person_name}" "{company_name}"'

        # Step 1: Collect raw results
        all_results = []
        seen_urls = set()

        search_queries = [
            f'{base_name} podcast',
            f'{base_name} interview',
            f'{base_name} conference OR talk OR keynote',
            f'{base_name} article OR blog',
        ]

        # Domains to exclude (social media, etc.)
        excluded_domains = [
            "linkedin.com", "facebook.com", "twitter.com", "x.com",
            "instagram.com", "tiktok.com", "pinterest.com"
        ]

        for query in search_queries:
            try:
                results = self.search(query, num_results=10)
                for r in results:
                    url = r.get("url", "")
                    if url and url not in seen_urls:
                        # Skip excluded domains
                        if any(domain in url.lower() for domain in excluded_domains):
                            continue
                        seen_urls.add(url)
                        all_results.append(r)
            except Exception as e:
                print(f"    Google search error for '{query}': {e}")

        # Step 2: Filter with LLM if enabled
        if use_llm_filter and all_results:
            try:
                from scripts.enrich.sources.relevance_filter import RelevanceFilter

                print(f"    Filtering {len(all_results)} results with LLM...")
                filter = RelevanceFilter()
                context = f"Founder/CEO of {company_name}" if company_name else f"Professional content about {person_name}"

                filtered_results = filter.filter_results(
                    person_name=person_name,
                    person_context=context,
                    results=all_results,
                    min_relevance_score=min_relevance_score
                )

                print(f"    → {len(filtered_results)} relevant results kept")
            except Exception as e:
                print(f"    LLM filter error: {e}, using raw results")
                filtered_results = all_results
        else:
            filtered_results = all_results

        # Step 3: Organize by category
        results = {
            "podcast_episodes": [],
            "video_appearances": [],
            "written_interviews": [],
            "articles": [],
            "talks": [],
            "all_results": filtered_results,
            "total_found": len(filtered_results),
            "total_raw": len(all_results)
        }

        for r in filtered_results:
            category = r.get("category", "article")
            url = r.get("url", "")

            if category == "podcast":
                results["podcast_episodes"].append(r)
            elif category == "interview":
                if "youtube.com" in url or "vimeo.com" in url:
                    results["video_appearances"].append(r)
                else:
                    results["written_interviews"].append(r)
            elif category == "talk":
                results["talks"].append(r)
            elif category in ("article", "own_content"):
                results["articles"].append(r)
            else:
                # Default: categorize by URL
                if "youtube.com" in url or "vimeo.com" in url:
                    results["video_appearances"].append(r)
                else:
                    results["articles"].append(r)

        return results

    def close(self):
        self.client.close()


# Quick test
if __name__ == "__main__":
    client = GoogleSearchClient()

    print("Searching for content about 'Yoshua Bengio'...")
    results = client.search_person_content("Yoshua Bengio", max_results_per_category=5)
    print(f"Total results found: {results['total_found']}")
    print(f"  - Podcasts: {len(results['podcasts'])}")
    print(f"  - Interviews: {len(results['interviews'])}")
    print(f"  - Articles: {len(results['articles'])}")
    print(f"  - Press: {len(results['press'])}")

    if results['all_results']:
        print("\nTop 5 results:")
        for r in results['all_results'][:5]:
            print(f"  [{r['category']}] {r['title']}")
            print(f"    {r['url']}")

    client.close()
