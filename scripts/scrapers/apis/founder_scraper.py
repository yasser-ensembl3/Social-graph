"""
Unified founder content scraper.

Combines all sources: Exa.ai + Jina, YouTube, Google Search
Outputs a single Markdown file with all findings.
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Load env
env_file = Path(__file__).parent.parent.parent.parent / ".env.local"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())

from .exa import ExaClient
from .jina import JinaReader
from .youtube import YouTubeClient
from .google_search import GoogleSearchClient


class FounderScraper:
    """
    Unified scraper that combines all sources.

    Sources:
    - Exa.ai: Blog posts, articles, podcasts (semantic search)
    - Jina: Full content extraction
    - YouTube: Video content
    - Google: Press mentions, interviews
    """

    def __init__(self):
        # Initialize clients
        self.exa = ExaClient()
        self.jina = JinaReader()

        self.youtube = None
        self.google = None

        try:
            self.youtube = YouTubeClient()
        except ValueError:
            print("[!] YouTube API not configured")

        try:
            self.google = GoogleSearchClient()
        except ValueError:
            print("[!] Google Search API not configured")

    def scrape_all(
        self,
        founder_name: str,
        company_name: Optional[str] = None,
        max_results_per_source: int = 5,
        fetch_content: bool = True
    ) -> dict:
        """
        Scrape all sources for a founder.

        Returns combined results from all sources.
        """
        print(f"\n{'='*60}")
        print(f"🔍 SCRAPING: {founder_name}")
        if company_name:
            print(f"   Company: {company_name}")
        print(f"{'='*60}\n")

        results = {
            "founder_name": founder_name,
            "company_name": company_name,
            "scraped_at": datetime.now().isoformat(),
            "exa": {"results": [], "total": 0},
            "youtube": {"results": [], "total": 0},
            "google": {"results": [], "total": 0},
            "content_fetched": []
        }

        # 1. Exa.ai - Semantic search for articles/blogs
        print("[1/3] 📚 Exa.ai - Articles & Blogs...")
        try:
            exa_results = self.exa.search_founder_content(
                founder_name=founder_name,
                company_name=company_name,
                num_results=max_results_per_source
            )
            results["exa"]["results"] = exa_results.get("results", [])
            results["exa"]["total"] = exa_results.get("total_found", 0)
            print(f"   ✓ Found {results['exa']['total']} results")
        except Exception as e:
            print(f"   ✗ Error: {e}")

        # 2. YouTube - Video content
        if self.youtube:
            print("\n[2/3] 🎬 YouTube - Videos...")
            try:
                yt_results = self.youtube.search_person_content(
                    person_name=founder_name,
                    max_results=max_results_per_source
                )
                results["youtube"]["results"] = yt_results.get("all_videos", [])
                results["youtube"]["total"] = yt_results.get("total_found", 0)
                print(f"   ✓ Found {results['youtube']['total']} videos")
            except Exception as e:
                print(f"   ✗ Error: {e}")
        else:
            print("\n[2/3] 🎬 YouTube - Skipped (not configured)")

        # 3. Google Search - Press & mentions
        if self.google:
            print("\n[3/3] 🔎 Google - Press & Mentions...")
            try:
                google_results = self.google.search_media_appearances(
                    person_name=founder_name,
                    company_name=company_name
                )
                results["google"]["results"] = google_results.get("all_results", [])
                results["google"]["total"] = google_results.get("total_found", 0)
                print(f"   ✓ Found {results['google']['total']} results")
            except Exception as e:
                print(f"   ✗ Error: {e}")
        else:
            print("\n[3/3] 🔎 Google - Skipped (not configured)")

        # 4. Fetch full content with Jina (from ALL sources)
        if fetch_content:
            print(f"\n[+] 📖 Fetching full content with Jina Reader...")

            # Collect URLs from Exa and Google (skip YouTube - it's video)
            urls_to_fetch = []
            seen_urls = set()

            # Exa URLs
            for r in results["exa"]["results"]:
                url = r.get("url")
                if url and url not in seen_urls:
                    urls_to_fetch.append({"url": url, "source": "exa", "title": r.get("title", "")})
                    seen_urls.add(url)

            # Google URLs
            for r in results["google"]["results"]:
                url = r.get("url")
                if url and url not in seen_urls:
                    # Skip social media and video platforms
                    skip_domains = ["youtube.com", "twitter.com", "x.com", "facebook.com", "linkedin.com", "instagram.com"]
                    if not any(domain in url.lower() for domain in skip_domains):
                        urls_to_fetch.append({"url": url, "source": "google", "title": r.get("title", "")})
                        seen_urls.add(url)

            # Limit total URLs to fetch
            urls_to_fetch = urls_to_fetch[:max_results_per_source * 2]

            print(f"   Scraping {len(urls_to_fetch)} URLs (Exa + Google)...\n")

            for i, item in enumerate(urls_to_fetch):
                url = item["url"]
                source = item["source"]
                print(f"   [{i+1}/{len(urls_to_fetch)}] [{source.upper()}] {url[:50]}...")
                try:
                    content = self.jina.read_url(url)
                    if content["success"]:
                        results["content_fetched"].append({
                            "url": url,
                            "source": source,
                            "title": content.get("title", "") or item.get("title", ""),
                            "content": content.get("content", ""),
                            "word_count": content.get("word_count", 0)
                        })
                        print(f"       ✓ {content['word_count']} words")
                    else:
                        print(f"       ✗ Failed: {content.get('error', 'Unknown')[:30]}")
                except Exception as e:
                    print(f"       ✗ Error: {e}")

        print(f"\n{'='*60}")
        print(f"✅ DONE - {results['exa']['total']} articles, {results['youtube']['total']} videos, {results['google']['total']} mentions")
        print(f"{'='*60}\n")

        return results

    def generate_markdown(self, results: dict) -> str:
        """Generate a Markdown report from scraped results."""

        founder = results["founder_name"]
        company = results.get("company_name", "")

        md = f"""# {founder}
{"*" + company + "*" if company else ""}

*Scraped: {results['scraped_at'][:10]}*

---

## 📊 Summary

| Source | Results |
|--------|---------|
| Articles & Blogs (Exa) | {results['exa']['total']} |
| YouTube Videos | {results['youtube']['total']} |
| Press & Mentions (Google) | {results['google']['total']} |

---

## 📚 Articles & Blog Posts

"""
        # Exa results
        if results["exa"]["results"]:
            for r in results["exa"]["results"]:
                md += f"### [{r.get('title', 'Untitled')}]({r.get('url', '')})\n"
                if r.get('published_date'):
                    md += f"*{r['published_date'][:10]}*\n"
                md += f"- Category: {r.get('category', 'article')}\n"
                md += "\n"
        else:
            md += "*No articles found*\n\n"

        # Content extracts (full content from Jina)
        if results["content_fetched"]:
            md += "---\n\n## 📖 Full Content (Scraped)\n\n"
            total_words = sum(c.get('word_count', 0) for c in results["content_fetched"])
            md += f"*{len(results['content_fetched'])} articles scraped, {total_words:,} words total*\n\n"

            for content in results["content_fetched"]:
                source_tag = content.get('source', 'unknown').upper()
                md += f"### {content['title']}\n"
                md += f"*{content['word_count']:,} words* | Source: **{source_tag}** | [Link]({content['url']})\n\n"

                # Full content (or truncated if very long)
                full_content = content['content'].strip()
                if len(full_content) > 5000:
                    md += f"{full_content[:5000]}\n\n*[... truncated, {len(full_content) - 5000:,} more characters]*\n\n"
                else:
                    md += f"{full_content}\n\n"

                md += "---\n\n"

        # YouTube
        md += "---\n\n## 🎬 YouTube Videos\n\n"
        if results["youtube"]["results"]:
            for v in results["youtube"]["results"][:10]:
                md += f"- **[{v.get('title', 'Untitled')}]({v.get('url', '')})**\n"
                md += f"  - Channel: {v.get('channel_title', 'Unknown')}\n"
                if v.get('published_at'):
                    md += f"  - Date: {v['published_at'][:10]}\n"
                md += "\n"
        else:
            md += "*No videos found*\n\n"

        # Google
        md += "---\n\n## 🔎 Press & Mentions\n\n"
        if results["google"]["results"]:
            for g in results["google"]["results"][:10]:
                md += f"- **[{g.get('title', 'Untitled')}]({g.get('url', '')})**\n"
                md += f"  - Source: {g.get('source', 'Unknown')}\n"
                if g.get('snippet'):
                    md += f"  - *{g['snippet'][:150]}...*\n"
                md += "\n"
        else:
            md += "*No press mentions found*\n\n"

        md += "---\n\n*Generated by Founder Scraper*\n"

        return md

    def scrape_and_save(
        self,
        founder_name: str,
        company_name: Optional[str] = None,
        output_dir: Optional[Path] = None,
        max_results: int = 5
    ) -> Path:
        """
        Scrape all sources and save as Markdown.

        Returns path to generated .md file.
        """
        # Scrape
        results = self.scrape_all(
            founder_name=founder_name,
            company_name=company_name,
            max_results_per_source=max_results
        )

        # Generate markdown
        markdown = self.generate_markdown(results)

        # Output path
        if output_dir is None:
            output_dir = Path(__file__).parent.parent.parent.parent / "data" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Filename
        safe_name = founder_name.lower().replace(' ', '-')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '-')
        filename = f"{safe_name}.md"
        output_path = output_dir / filename

        # Save
        output_path.write_text(markdown, encoding='utf-8')
        print(f"📄 Saved to: {output_path}")

        # Also save raw JSON
        json_path = output_dir.parent / "cache" / f"{safe_name}_raw.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str))
        print(f"📦 Raw data: {json_path}")

        return output_path

    def close(self):
        self.exa.close()
        self.jina.close()
        if self.youtube:
            self.youtube.close()
        if self.google:
            self.google.close()


# CLI
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python founder_scraper.py <founder_name> [company_name] [--max=5]")
        print("")
        print("Examples:")
        print("  python founder_scraper.py 'Elon Musk' 'Tesla'")
        print("  python founder_scraper.py 'Sam Altman' 'OpenAI' --max=10")
        print("  python founder_scraper.py 'Naval Ravikant'")
        sys.exit(1)

    founder_name = sys.argv[1]
    company_name = None
    max_results = 5

    for arg in sys.argv[2:]:
        if arg.startswith('--max='):
            max_results = int(arg.split('=')[1])
        elif not arg.startswith('--'):
            company_name = arg

    scraper = FounderScraper()

    try:
        output_path = scraper.scrape_and_save(
            founder_name=founder_name,
            company_name=company_name,
            max_results=max_results
        )

        print(f"\n✅ Profile generated: {output_path}")

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        scraper.close()
