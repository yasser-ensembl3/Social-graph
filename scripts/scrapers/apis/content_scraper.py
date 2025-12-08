"""
Combined content scraper for founders.

Pipeline: Exa (search) → Jina (read content) → Structured output
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from .exa import ExaClient
from .jina import JinaReader


class FounderContentScraper:
    """
    Scrapes articles, blogs, and podcasts about a founder.

    1. Exa.ai finds relevant URLs
    2. Jina Reader extracts content from each URL
    3. Returns structured data with full content
    """

    def __init__(self):
        self.exa = ExaClient()
        self.jina = JinaReader()

    def scrape(
        self,
        founder_name: str,
        company_name: Optional[str] = None,
        num_results: int = 10,
        read_content: bool = True
    ) -> dict:
        """
        Search and scrape content about a founder.

        Args:
            founder_name: Full name of the founder
            company_name: Optional company name
            num_results: Max URLs to find
            read_content: Whether to fetch full content with Jina

        Returns:
            Dict with all results and content
        """
        print(f"\n{'='*60}")
        print(f"Scraping content for: {founder_name}")
        if company_name:
            print(f"Company: {company_name}")
        print(f"{'='*60}\n")

        # Step 1: Search with Exa
        print("[1/2] Searching with Exa.ai...")
        search_results = self.exa.search_founder_content(
            founder_name=founder_name,
            company_name=company_name,
            num_results=num_results
        )

        print(f"  Found {search_results['total_found']} results")
        print(f"    - Blogs: {len(search_results['blogs'])}")
        print(f"    - Articles: {len(search_results['articles'])}")
        print(f"    - Podcasts: {len(search_results['podcasts'])}")
        print(f"    - Videos: {len(search_results['videos'])}")

        # Step 2: Read content with Jina
        contents = []
        if read_content and search_results['results']:
            print(f"\n[2/2] Reading content with Jina Reader...")

            for i, result in enumerate(search_results['results']):
                url = result.get('url')
                if not url:
                    continue

                print(f"\n  [{i+1}/{len(search_results['results'])}] {result['title'][:50]}...")

                content = self.jina.read_url(url)

                if content['success']:
                    print(f"    ✓ {content['word_count']} words")
                    contents.append({
                        **result,
                        "content": content['content'],
                        "word_count": content['word_count'],
                        "scraped": True
                    })
                else:
                    print(f"    ✗ Failed: {content['error'][:40]}")
                    contents.append({
                        **result,
                        "content": None,
                        "error": content['error'],
                        "scraped": False
                    })
        else:
            contents = search_results['results']

        # Build final output
        output = {
            "founder_name": founder_name,
            "company_name": company_name,
            "scraped_at": datetime.now().isoformat(),
            "query": search_results['query'],
            "total_found": len(contents),
            "total_scraped": len([c for c in contents if c.get('scraped')]),
            "contents": contents,
            "by_category": {
                "blogs": [c for c in contents if c.get('category') == 'blog'],
                "articles": [c for c in contents if c.get('category') == 'article'],
                "podcasts": [c for c in contents if c.get('category') == 'podcast'],
                "videos": [c for c in contents if c.get('category') == 'video']
            }
        }

        print(f"\n{'='*60}")
        print(f"Done! Scraped {output['total_scraped']}/{output['total_found']} URLs")
        print(f"{'='*60}\n")

        return output

    def scrape_and_save(
        self,
        founder_name: str,
        company_name: Optional[str] = None,
        output_dir: Optional[Path] = None,
        num_results: int = 10
    ) -> Path:
        """
        Scrape content and save to JSON file.

        Returns:
            Path to saved JSON file
        """
        # Scrape
        data = self.scrape(
            founder_name=founder_name,
            company_name=company_name,
            num_results=num_results
        )

        # Output path
        if output_dir is None:
            output_dir = Path(__file__).parent.parent.parent.parent / "data" / "cache"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        safe_name = founder_name.lower().replace(' ', '_')
        filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = output_dir / filename

        # Save
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"Saved to: {output_path}")

        return output_path

    def close(self):
        self.exa.close()
        self.jina.close()


# CLI
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python content_scraper.py <founder_name> [company_name] [--num=10] [--no-content]")
        print("")
        print("Examples:")
        print("  python content_scraper.py 'Elon Musk' 'Tesla'")
        print("  python content_scraper.py 'Sam Altman' 'OpenAI' --num=5")
        print("  python content_scraper.py 'Naval Ravikant' --no-content")
        sys.exit(1)

    founder_name = sys.argv[1]
    company_name = None
    num_results = 10
    read_content = True

    # Parse args
    for arg in sys.argv[2:]:
        if arg.startswith('--num='):
            num_results = int(arg.split('=')[1])
        elif arg == '--no-content':
            read_content = False
        elif not arg.startswith('--'):
            company_name = arg

    scraper = FounderContentScraper()

    try:
        output_path = scraper.scrape_and_save(
            founder_name=founder_name,
            company_name=company_name,
            num_results=num_results
        )

        # Show summary
        data = json.loads(output_path.read_text())

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)

        for content in data['contents'][:5]:
            status = "✓" if content.get('scraped') else "✗"
            words = content.get('word_count', 0)
            print(f"\n{status} [{content['category'].upper()}] {content['title'][:50]}")
            print(f"  URL: {content['url'][:60]}")
            if words:
                print(f"  Words: {words}")

        if len(data['contents']) > 5:
            print(f"\n... and {len(data['contents']) - 5} more results")

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        scraper.close()
