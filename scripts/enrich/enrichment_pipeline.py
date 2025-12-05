#!/usr/bin/env python3
"""
Main enrichment pipeline for founder profiles.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.parse.linkedin_parser import parse_linkedin_md
from scripts.parse.models import FounderProfile
from scripts.enrich.sources.phantombuster import PhantombusterClient
from scripts.enrich.sources.youtube import YouTubeClient
from scripts.enrich.sources.google_search import GoogleSearchClient
from scripts.enrich.sources.podcasts import ListenNotesClient
from scripts.synthesize.llm_synthesizer import generate_enriched_profile


class FounderEnrichmentPipeline:
    """Pipeline to enrich a single founder profile."""

    def __init__(self, use_phantombuster: bool = True):
        self.use_phantombuster = use_phantombuster
        if use_phantombuster:
            self.pb_client = PhantombusterClient()
        else:
            self.pb_client = None

        # Initialize media content clients (optional - will skip if not configured)
        self.youtube_client = None
        self.google_client = None
        self.podcast_client = None

        try:
            self.youtube_client = YouTubeClient()
        except ValueError:
            print("  [!] YouTube API not configured (YOUTUBE_API_KEY missing)")

        try:
            self.google_client = GoogleSearchClient()
        except ValueError:
            print("  [!] Google Search API not configured (GOOGLE_API_KEY or GOOGLE_SEARCH_ENGINE_ID missing)")

        try:
            self.podcast_client = ListenNotesClient()
        except ValueError:
            print("  [!] Listen Notes API not configured (LISTENNOTES_API_KEY missing)")

    def enrich_profile(self, profile: FounderProfile, skip_phantombuster: bool = False) -> dict:
        """Collect enrichment data from all sources."""
        enriched_data = {
            "linkedin_full": {},
            "linkedin_posts": [],
            "youtube_results": {},
            "google_results": {},
            "podcast_results": {},
            "sources_used": []
        }

        print(f"\nEnriching: {profile.name}")

        # 1. LinkedIn Profile Scraper (Phantombuster)
        if not skip_phantombuster and self.pb_client and profile.linkedin_url:
            try:
                print("  - Fetching LinkedIn profile (Phantombuster)...")
                linkedin_data = self.pb_client.scrape_linkedin_profile(profile.linkedin_url)
                enriched_data["linkedin_full"] = linkedin_data
                enriched_data["sources_used"].append("linkedin_profile")
                print(f"    ✓ LinkedIn profile: OK")
            except Exception as e:
                print(f"    ✗ LinkedIn profile error: {e}")

            # 2. LinkedIn Activity Extractor (Phantombuster)
            try:
                print("  - Fetching LinkedIn activity (Phantombuster)...")
                activity_data = self.pb_client.scrape_linkedin_activity(profile.linkedin_url, max_posts=25)
                enriched_data["linkedin_posts"] = activity_data
                enriched_data["sources_used"].append("linkedin_activity")
                print(f"    ✓ LinkedIn activity: OK")
            except Exception as e:
                print(f"    ✗ LinkedIn activity error: {e}")
        else:
            print("  - Skipping Phantombuster enrichment")

        # 3. YouTube - Find video content about the person
        if self.youtube_client:
            try:
                print("  - Searching YouTube for video content...")
                youtube_data = self.youtube_client.search_person_content(profile.name, max_results=10)
                enriched_data["youtube_results"] = youtube_data
                enriched_data["sources_used"].append("youtube")
                print(f"    ✓ YouTube: {youtube_data['total_found']} videos found")
            except Exception as e:
                print(f"    ✗ YouTube error: {e}")

        # 4. Google Search - Find articles, interviews, press mentions
        if self.google_client:
            try:
                print("  - Searching Google for media appearances...")
                company_name = profile.current_position.company if profile.current_position else None
                google_data = self.google_client.search_media_appearances(profile.name, company_name)
                enriched_data["google_results"] = google_data
                enriched_data["sources_used"].append("google_search")
                print(f"    ✓ Google: {google_data['total_found']} results found")
            except Exception as e:
                print(f"    ✗ Google Search error: {e}")

        # 5. Podcasts - Find podcast appearances
        if self.podcast_client:
            try:
                print("  - Searching for podcast appearances...")
                podcast_data = self.podcast_client.search_person_appearances(profile.name, max_results=15)
                enriched_data["podcast_results"] = podcast_data
                enriched_data["sources_used"].append("podcasts")
                print(f"    ✓ Podcasts: {podcast_data['total_found']} episodes found")
            except Exception as e:
                print(f"    ✗ Podcast search error: {e}")

        return enriched_data

    def run(self, input_md: Path, output_md: Path, skip_phantombuster: bool = False) -> str:
        """Run full enrichment pipeline on a single profile."""

        # 1. Parse the LinkedIn .md
        print(f"Parsing: {input_md}")
        profile = parse_linkedin_md(input_md)
        print(f"  Name: {profile.name}")
        print(f"  Company: {profile.current_position.company if profile.current_position else 'N/A'}")
        print(f"  LinkedIn: {profile.linkedin_url}")

        # 2. Enrich with external data
        enriched_data = self.enrich_profile(profile, skip_phantombuster=skip_phantombuster)

        # 3. Generate enriched markdown via LLM
        print("\nGenerating enriched profile via LLM...")
        markdown = generate_enriched_profile(profile, enriched_data, output_md)

        print(f"\nDone! Output: {output_md}")
        return markdown

    def close(self):
        if self.pb_client:
            self.pb_client.close()
        if self.youtube_client:
            self.youtube_client.close()
        if self.google_client:
            self.google_client.close()
        if self.podcast_client:
            self.podcast_client.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Enrich a founder profile")
    parser.add_argument("input", type=Path, help="Input LinkedIn .md file")
    parser.add_argument("-o", "--output", type=Path, help="Output enriched .md file")
    parser.add_argument("--no-phantombuster", action="store_true", help="Skip Phantombuster enrichment")
    args = parser.parse_args()

    # Default output path
    if not args.output:
        args.output = args.input.parent / f"{args.input.stem}_enriched.md"

    pipeline = FounderEnrichmentPipeline(use_phantombuster=not args.no_phantombuster)

    try:
        pipeline.run(args.input, args.output, skip_phantombuster=args.no_phantombuster)
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
