"""
Test script: Generate .md files from existing scraper data.
Uses data from:
- LinkedIn Profile/Activity (Phantombuster)
- YouTube results
- Google Search results
"""
import json
from pathlib import Path
from to_markdown import MarkdownTransformer

# Paths
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"


def test_linkedin_profile():
    """Generate .md from LinkedIn profile data."""
    print("\n=== LinkedIn Profile ===")

    profile_file = RAW_DIR / "ilyas_linkedin_profile.json"
    if not profile_file.exists():
        print(f"  [!] File not found: {profile_file}")
        return

    with open(profile_file) as f:
        profiles = json.load(f)

    transformer = MarkdownTransformer()

    for profile in profiles:
        name = f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip()
        slug = transformer._slugify(name)

        # Create profile markdown
        md_content = f"""---
source_type: linkedin_profile
url: {profile.get('profileUrl', '')}
scraped_at: {profile.get('refreshedAt', '')}
---

# {name}

**{profile.get('linkedinHeadline', '')}**

## About
{profile.get('linkedinDescription', '')}

## Current Role
- **Company:** {profile.get('companyName', '')}
- **Title:** {profile.get('linkedinJobTitle', '')}
- **Location:** {profile.get('location', '')}

## Previous Role
- **Company:** {profile.get('previousCompanyName', '')}
- **Title:** {profile.get('linkedinPreviousJobTitle', '')}

## Education
- **School:** {profile.get('linkedinSchoolName', '')}
- **Degree:** {profile.get('linkedinSchoolDegree', '')}

## Skills
{profile.get('linkedinSkillsLabel', '')}

## Stats
- **Followers:** {profile.get('linkedinFollowersCount', 0):,}
- **Connections:** {profile.get('linkedinConnectionsCount', 0):,}

[LinkedIn Profile]({profile.get('profileUrl', '')})
"""
        # Save
        person_dir = transformer.output_dir / slug
        person_dir.mkdir(parents=True, exist_ok=True)

        filepath = person_dir / "linkedin_profile_000.md"
        filepath.write_text(md_content, encoding="utf-8")
        print(f"  → {filepath}")


def test_linkedin_activity():
    """Generate .md from LinkedIn activity data."""
    print("\n=== LinkedIn Activity ===")

    activity_file = RAW_DIR / "ilyas_linkedin_activity.json"
    if not activity_file.exists():
        print(f"  [!] File not found: {activity_file}")
        return

    with open(activity_file) as f:
        posts = json.load(f)

    transformer = MarkdownTransformer()

    # Get author from first post
    if posts:
        author = posts[0].get("author", "Unknown")
        slug = transformer._slugify(author)
        person_dir = transformer.output_dir / slug
        person_dir.mkdir(parents=True, exist_ok=True)

        # Limit to first 20 posts for test
        for i, post in enumerate(posts[:20]):
            md_content = f"""---
source_type: linkedin_post
url: {post.get('postUrl', '')}
published_at: {post.get('postTimestamp', '')}
type: {post.get('type', '')}
---

# LinkedIn Post

**Author:** {post.get('author', '')}
**Date:** {post.get('postDate', '')}
**Type:** {post.get('type', '')}

---

{post.get('postContent', '')}

---

**Engagement:**
- Likes: {post.get('likeCount', 0)}
- Comments: {post.get('commentCount', 0)}
- Reposts: {post.get('repostCount', 0)}

[View on LinkedIn]({post.get('postUrl', '')})
"""
            filepath = person_dir / f"linkedin_post_{i:03d}.md"
            filepath.write_text(md_content, encoding="utf-8")

        print(f"  → Saved {min(20, len(posts))} posts to {person_dir}")


def test_youtube_google():
    """Generate .md from YouTube and Google search results."""
    print("\n=== YouTube & Google Search ===")

    enrichment_file = DATA_DIR / "full_enrichment_test.json"
    if not enrichment_file.exists():
        print(f"  [!] File not found: {enrichment_file}")
        return

    with open(enrichment_file) as f:
        data = json.load(f)

    transformer = MarkdownTransformer()

    for person_name, results in data.items():
        slug = transformer._slugify(person_name)
        person_dir = transformer.output_dir / slug
        person_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n  {person_name}:")

        # YouTube videos
        yt_data = results.get("youtube", {})
        videos = yt_data.get("videos", [])
        for i, video in enumerate(videos):
            md_content = f"""---
source_type: youtube
url: {video.get('url', '')}
published_at: {video.get('published_at', '')}
channel: {video.get('channel_title', '')}
category: {video.get('category', '')}
relevance_score: {video.get('relevance_score', '')}
---

# {video.get('title', 'Untitled')}

**Channel:** {video.get('channel_title', '')}
**Published:** {video.get('published_at', '')}

{video.get('description', '')}

[Watch on YouTube]({video.get('url', '')})
"""
            filepath = person_dir / f"youtube_{i:03d}_{transformer._slugify(video.get('title', 'untitled'))[:30]}.md"
            filepath.write_text(md_content, encoding="utf-8")

        print(f"    → {len(videos)} YouTube videos")

        # Google results
        google_data = results.get("google", {})
        google_results = google_data.get("top_results", [])
        for i, result in enumerate(google_results):
            md_content = f"""---
source_type: google_search
url: {result.get('url', '')}
domain: {result.get('source', '')}
category: {result.get('category', '')}
relevance_score: {result.get('relevance_score', '')}
---

# {result.get('title', 'Untitled')}

**Source:** {result.get('source', '')}

{result.get('snippet', '')}

[View Source]({result.get('url', '')})
"""
            filepath = person_dir / f"google_{i:03d}_{transformer._slugify(result.get('title', 'untitled'))[:30]}.md"
            filepath.write_text(md_content, encoding="utf-8")

        print(f"    → {len(google_results)} Google results")


def main():
    print("=" * 50)
    print("Test: Generating .md files from existing data")
    print("=" * 50)

    test_linkedin_profile()
    test_linkedin_activity()
    test_youtube_google()

    print("\n" + "=" * 50)
    print("Done! Check data/raw_content/ for generated files")
    print("=" * 50)


if __name__ == "__main__":
    main()
