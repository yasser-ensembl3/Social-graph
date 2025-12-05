"""
Phantombuster API client for enrichment.
"""
import os
import time
import json
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


class PhantombusterClient:
    """Client for Phantombuster API."""

    BASE_URL = "https://api.phantombuster.com/api/v2"

    # Known Phantom IDs (configure these in your account)
    PHANTOMS = {
        "linkedin_profile": "604025905972590",    # LinkedIn Profile Scraper
        "linkedin_activity": "7643306922532979",  # LinkedIn Activity Extractor
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("PHANTOMBUSTER_API_KEY")
        if not self.api_key:
            raise ValueError("PHANTOMBUSTER_API_KEY required")

        self.client = httpx.Client(
            headers={"X-Phantombuster-Key-1": self.api_key},
            timeout=60.0
        )

    def get_phantom(self, phantom_id: str) -> dict:
        """Get Phantom details."""
        resp = self.client.get(f"{self.BASE_URL}/agents/fetch", params={"id": phantom_id})
        resp.raise_for_status()
        return resp.json()

    def launch_phantom(self, phantom_id: str, arguments: Optional[dict] = None) -> dict:
        """Launch a Phantom with optional arguments.

        If arguments is None, the Phantom will use its configured input
        (e.g., spreadsheet URL configured in PhantomBuster dashboard).
        """
        payload = {"id": phantom_id}
        if arguments:
            payload["argument"] = json.dumps(arguments)

        resp = self.client.post(f"{self.BASE_URL}/agents/launch", json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_output(self, phantom_id: str) -> Optional[dict]:
        """Get Phantom output/results."""
        resp = self.client.get(
            f"{self.BASE_URL}/agents/fetch-output",
            params={"id": phantom_id}
        )
        resp.raise_for_status()
        return resp.json()

    def wait_for_completion(self, phantom_id: str, timeout: int = 300, poll_interval: int = 10) -> dict:
        """Wait for Phantom to complete and return results."""
        start = time.time()
        initial_launches = None

        while time.time() - start < timeout:
            status = self.get_phantom(phantom_id)
            nb_launches = status.get("nbLaunches", 0)
            last_end_type = status.get("lastEndType")

            # First iteration: record the initial launch count
            if initial_launches is None:
                initial_launches = nb_launches

            # Check if a new run completed (launch count increased and status is finished)
            if nb_launches > initial_launches and last_end_type == "finished":
                print(f"    Phantom completed (launches: {nb_launches})")
                return self.get_output(phantom_id)
            elif nb_launches > initial_launches and last_end_type == "error":
                raise Exception(f"Phantom failed: {status.get('lastEndMessage', 'Unknown error')}")

            elapsed = int(time.time() - start)
            print(f"    Waiting... ({elapsed}s / {timeout}s)")
            time.sleep(poll_interval)

        raise TimeoutError(f"Phantom did not complete within {timeout}s")

    def scrape_linkedin_profile(self, linkedin_url: Optional[str] = None) -> dict:
        """Scrape LinkedIn profile(s).

        Args:
            linkedin_url: Optional single URL. If None, uses spreadsheet configured in PhantomBuster.
        """
        phantom_id = self.PHANTOMS.get("linkedin_profile")
        if not phantom_id:
            raise ValueError("LinkedIn Profile Phantom not configured")

        # Launch with URL or use spreadsheet
        if linkedin_url:
            self.launch_phantom(phantom_id, {
                "profileUrls": [linkedin_url],
                "numberOfAddsPerLaunch": 1
            })
        else:
            # Use spreadsheet configured in PhantomBuster dashboard
            self.launch_phantom(phantom_id)

        # Wait and get results
        return self.wait_for_completion(phantom_id)

    def scrape_linkedin_activity(self, linkedin_url: Optional[str] = None, max_posts: int = 50) -> dict:
        """Scrape LinkedIn posts/articles.

        Args:
            linkedin_url: Optional single URL. If None, uses spreadsheet configured in PhantomBuster.
            max_posts: Maximum posts to scrape per profile.
        """
        phantom_id = self.PHANTOMS.get("linkedin_activity")
        if not phantom_id:
            raise ValueError("LinkedIn Activity Phantom not configured")

        # Launch with URL or use spreadsheet
        if linkedin_url:
            self.launch_phantom(phantom_id, {
                "profileUrls": [linkedin_url],
                "numberMaxOfPosts": max_posts
            })
        else:
            # Use spreadsheet configured in PhantomBuster dashboard
            self.launch_phantom(phantom_id)

        # Wait and get results
        return self.wait_for_completion(phantom_id)

    def run_profile_scraper_batch(self, timeout: int = 300) -> dict:
        """Run LinkedIn Profile Scraper using config set in PhantomBuster dashboard.

        Args:
            timeout: Max wait time in seconds

        The Phantom uses whatever is configured in PhantomBuster (spreadsheet, limits, etc.)
        """
        phantom_id = self.PHANTOMS.get("linkedin_profile")
        if not phantom_id:
            raise ValueError("LinkedIn Profile Phantom not configured")

        print("  → Launching LinkedIn Profile Scraper (using PhantomBuster config)...")
        self.launch_phantom(phantom_id)  # No arguments - use dashboard config
        return self.wait_for_completion(phantom_id, timeout=timeout)

    def run_activity_scraper_batch(self, timeout: int = 300) -> dict:
        """Run LinkedIn Activity Extractor using config set in PhantomBuster dashboard.

        Args:
            timeout: Max wait time in seconds

        The Phantom uses whatever is configured in PhantomBuster (spreadsheet, limits, etc.)
        """
        phantom_id = self.PHANTOMS.get("linkedin_activity")
        if not phantom_id:
            raise ValueError("LinkedIn Activity Phantom not configured")

        print("  → Launching LinkedIn Activity Extractor (using PhantomBuster config)...")
        self.launch_phantom(phantom_id)  # No arguments - use dashboard config
        return self.wait_for_completion(phantom_id, timeout=timeout)

    def close(self):
        self.client.close()


# Quick test
if __name__ == "__main__":
    client = PhantombusterClient()

    # Check configured phantom
    phantom = client.get_phantom(client.PHANTOMS["linkedin_profile"])
    print(f"Phantom: {phantom.get('name')}")
    print(f"Last run: {phantom.get('lastEndStatus', 'never')}")

    client.close()
