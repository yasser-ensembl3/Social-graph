"""
Batch scraper for founders from CSV file.
Scrapes all founders one by one and saves individual .md files.
"""
import csv
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.scrapers.apis.founder_scraper import FounderScraper


def notify_macos(title: str, message: str):
    """Send macOS notification."""
    try:
        subprocess.run([
            'osascript', '-e',
            f'display notification "{message}" with title "{title}"'
        ], check=True)
    except Exception:
        pass  # Ignore notification errors


def batch_scrape(csv_path: str, max_results: int = 5, start_from: int = 0):
    """
    Scrape all founders from CSV file.

    Args:
        csv_path: Path to CSV file
        max_results: Max results per source per founder
        start_from: Index to start from (for resuming)
    """
    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        founders = list(reader)

    total = len(founders)
    print(f"\n{'='*60}")
    print(f"🚀 BATCH SCRAPER - {total} founders")
    print(f"{'='*60}\n")

    # Initialize scraper
    scraper = FounderScraper()

    # Stats
    success = 0
    failed = 0
    skipped = 0
    start_time = datetime.now()

    # Process each founder
    for i, row in enumerate(founders):
        # Skip if before start_from
        if i < start_from:
            continue

        # Extract name and company
        first_name = row.get('firstName', '').strip()
        last_name = row.get('lastName', '').strip()
        company = row.get('companyName', '').strip()

        full_name = f"{first_name} {last_name}".strip()

        if not full_name:
            print(f"[{i+1}/{total}] ⏭️  Skipped (no name)")
            skipped += 1
            continue

        # Check if already scraped
        safe_name = full_name.lower().replace(' ', '-')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '-')
        output_path = Path(__file__).parent.parent / "data" / "output" / f"{safe_name}.md"

        if output_path.exists():
            print(f"[{i+1}/{total}] ⏭️  {full_name} - Already exists")
            skipped += 1
            continue

        # Scrape
        print(f"\n[{i+1}/{total}] 🔍 {full_name} ({company})")
        print("-" * 40)

        try:
            scraper.scrape_and_save(
                founder_name=full_name,
                company_name=company if company else None,
                max_results=max_results
            )
            success += 1
            print(f"✅ Done: {full_name}")

        except Exception as e:
            failed += 1
            print(f"❌ Error: {full_name} - {e}")

        # Notification every 10 founders
        if (success + failed) % 10 == 0 and (success + failed) > 0:
            elapsed = datetime.now() - start_time
            rate = (success + failed) / elapsed.total_seconds() * 60  # per minute
            remaining = total - (i + 1)
            eta_minutes = remaining / rate if rate > 0 else 0

            msg = f"✅ {success} OK, ❌ {failed} failed, ⏭️ {skipped} skipped"
            notify_macos(
                f"Scraping: {i+1}/{total}",
                msg
            )
            print(f"\n📊 Progress: {i+1}/{total} | {msg}")
            print(f"⏱️  Rate: {rate:.1f}/min | ETA: {eta_minutes:.0f} min\n")

        # Small delay to avoid rate limiting
        time.sleep(1)

    # Final stats
    elapsed = datetime.now() - start_time

    print(f"\n{'='*60}")
    print(f"🏁 FINISHED")
    print(f"{'='*60}")
    print(f"✅ Success: {success}")
    print(f"❌ Failed: {failed}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"⏱️  Duration: {elapsed}")
    print(f"{'='*60}\n")

    # Final notification
    notify_macos(
        "Scraping terminé !",
        f"✅ {success} OK, ❌ {failed} failed, ⏭️ {skipped} skipped"
    )

    scraper.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch scrape founders from CSV")
    parser.add_argument("csv", type=str, help="Path to CSV file")
    parser.add_argument("--max", type=int, default=5, help="Max results per source")
    parser.add_argument("--start", type=int, default=0, help="Start from index (for resuming)")

    args = parser.parse_args()

    batch_scrape(args.csv, max_results=args.max, start_from=args.start)
