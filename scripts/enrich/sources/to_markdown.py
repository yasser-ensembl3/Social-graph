"""
Transform raw scraper results to Markdown files.
LLM does a simple relevance check (keep/discard) before writing.
"""
import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from openai import OpenAI

# Load env
env_file = Path(__file__).parent.parent.parent.parent / ".env.local"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())


class MarkdownTransformer:
    """
    Transform raw results to Markdown with lightweight LLM relevance check.
    No scoring - just binary: relevant or not.
    """

    def __init__(self, output_dir: Optional[Path] = None, api_key: Optional[str] = None):
        self.output_dir = output_dir or Path(__file__).parent.parent.parent.parent / "data" / "enriched"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            print("[!] No OPENAI_API_KEY - skipping relevance check")

    def check_relevance_batch(
        self,
        person_name: str,
        person_context: str,
        results: list[dict]
    ) -> list[dict]:
        """
        Quick binary relevance check: is this about the right person?
        Returns only relevant results.
        """
        if not self.client or not results:
            return results  # No filtering if no API key

        # Format results for prompt
        results_text = []
        for i, r in enumerate(results):
            title = r.get("title", "N/A")
            desc = (r.get("description") or r.get("snippet") or "")[:150]
            source = r.get("channel_title") or r.get("source") or r.get("display_url") or "N/A"
            results_text.append(f"[{i}] {title} | {source} | {desc}")

        prompt = f"""Vérifie si ces résultats concernent vraiment cette personne:

PERSONNE: {person_name}
CONTEXTE: {person_context}

RÉSULTATS:
{chr(10).join(results_text)}

Pour chaque résultat, réponds simplement:
- "keep" si ça parle bien de cette personne (même mention légère = keep)
- "discard" si c'est clairement un homonyme ou sans rapport

Réponds en JSON: {{"decisions": [{{"index": 0, "action": "keep"}}, ...]}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Réponds uniquement en JSON valide."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1000
            )

            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            decisions = json.loads(content)["decisions"]

            # Keep only relevant results
            kept = []
            discarded_count = 0
            for d in decisions:
                idx = d["index"]
                if idx < len(results) and d["action"] == "keep":
                    kept.append(results[idx])
                else:
                    discarded_count += 1

            if discarded_count > 0:
                print(f"    → Discarded {discarded_count} irrelevant results")

            return kept

        except Exception as e:
            print(f"  [!] Relevance check error: {e}")
            return results  # Keep all on error

    def result_to_markdown(self, result: dict, source_type: str) -> str:
        """Convert a single result to markdown format."""

        title = result.get("title", "Untitled")
        url = result.get("url", "")
        description = result.get("description") or result.get("snippet") or ""

        # Build metadata section
        metadata = []
        metadata.append(f"source_type: {source_type}")
        metadata.append(f"url: {url}")
        metadata.append(f"scraped_at: {datetime.now().isoformat()}")

        if result.get("channel_title"):
            metadata.append(f"channel: {result['channel_title']}")
        if result.get("published_at"):
            metadata.append(f"published: {result['published_at']}")
        if result.get("source"):
            metadata.append(f"domain: {result['source']}")
        if result.get("category"):
            metadata.append(f"category: {result['category']}")

        # Build markdown
        md = f"""---
{chr(10).join(metadata)}
---

# {title}

{description}

[Source]({url})
"""
        return md

    def save_result(self, result: dict, person_slug: str, source_type: str, index: int) -> Path:
        """Save a single result as markdown file."""

        # Create person directory
        person_dir = self.output_dir / person_slug
        person_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        title_slug = self._slugify(result.get("title", "untitled"))[:50]
        filename = f"{source_type}_{index:03d}_{title_slug}.md"

        filepath = person_dir / filename
        md_content = self.result_to_markdown(result, source_type)
        filepath.write_text(md_content, encoding="utf-8")

        return filepath

    def transform_youtube_results(
        self,
        person_name: str,
        person_context: str,
        results: dict,
        person_slug: Optional[str] = None
    ) -> list[Path]:
        """
        Transform YouTube search results to markdown files.

        Args:
            person_name: Full name
            person_context: Brief description for relevance check
            results: Output from YouTubeClient.search_person_content()
            person_slug: Directory name (defaults to slugified name)
        """
        slug = person_slug or self._slugify(person_name)
        all_videos = results.get("all_videos", [])

        print(f"  Processing {len(all_videos)} YouTube results for {person_name}...")

        # Check relevance
        relevant = self.check_relevance_batch(person_name, person_context, all_videos)

        # Save to markdown
        saved = []
        for i, video in enumerate(relevant):
            path = self.save_result(video, slug, "youtube", i)
            saved.append(path)

        print(f"  → Saved {len(saved)} markdown files")
        return saved

    def transform_google_results(
        self,
        person_name: str,
        person_context: str,
        results: dict,
        person_slug: Optional[str] = None
    ) -> list[Path]:
        """
        Transform Google Search results to markdown files.

        Args:
            person_name: Full name
            person_context: Brief description for relevance check
            results: Output from GoogleSearchClient.search_media_appearances()
            person_slug: Directory name (defaults to slugified name)
        """
        slug = person_slug or self._slugify(person_name)
        all_results = results.get("all_results", [])

        print(f"  Processing {len(all_results)} Google results for {person_name}...")

        # Check relevance
        relevant = self.check_relevance_batch(person_name, person_context, all_results)

        # Save to markdown
        saved = []
        for i, result in enumerate(relevant):
            path = self.save_result(result, slug, "google", i)
            saved.append(path)

        print(f"  → Saved {len(saved)} markdown files")
        return saved

    def transform_phantombuster_results(
        self,
        person_name: str,
        results: dict,
        person_slug: Optional[str] = None
    ) -> list[Path]:
        """
        Transform Phantombuster LinkedIn results to markdown files.
        No relevance check needed - LinkedIn data is already targeted.
        """
        slug = person_slug or self._slugify(person_name)

        saved = []

        # Handle profile data
        if "output" in results:
            output = results.get("output", {})

            # Profile data
            if isinstance(output, dict):
                path = self.save_result({
                    "title": f"LinkedIn Profile - {person_name}",
                    "description": json.dumps(output, indent=2, ensure_ascii=False),
                    "url": output.get("linkedInUrl", ""),
                    "category": "linkedin_profile"
                }, slug, "linkedin_profile", 0)
                saved.append(path)

            # Activity/posts data (list)
            elif isinstance(output, list):
                for i, post in enumerate(output):
                    path = self.save_result({
                        "title": post.get("postContent", "LinkedIn Post")[:100],
                        "description": post.get("postContent", ""),
                        "url": post.get("postUrl", ""),
                        "published_at": post.get("postDate"),
                        "category": "linkedin_post"
                    }, slug, "linkedin_post", i)
                    saved.append(path)

        print(f"  → Saved {len(saved)} LinkedIn markdown files")
        return saved

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug."""
        import re
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text[:100]


# Quick test
if __name__ == "__main__":
    transformer = MarkdownTransformer()

    # Test with sample data
    test_results = {
        "all_videos": [
            {
                "title": "Interview with Yoshua Bengio on AI Safety",
                "description": "Deep discussion about AI alignment and safety research",
                "channel_title": "Lex Fridman",
                "url": "https://youtube.com/watch?v=abc123",
                "published_at": "2024-01-15"
            },
            {
                "title": "Random cooking video",
                "description": "How to make pasta",
                "channel_title": "Chef John",
                "url": "https://youtube.com/watch?v=xyz789"
            }
        ]
    }

    print("Testing markdown transformer...")
    saved = transformer.transform_youtube_results(
        person_name="Yoshua Bengio",
        person_context="AI researcher, deep learning pioneer, Mila founder",
        results=test_results,
        person_slug="yoshua-bengio"
    )

    print(f"\nSaved files:")
    for p in saved:
        print(f"  {p}")
