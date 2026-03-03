# Founders Graph

Multi-source web scraping and enrichment pipeline for building comprehensive founder profiles. Aggregates data from articles, blogs, podcasts, YouTube videos, LinkedIn, and press mentions into structured Markdown profiles with optional LLM-powered synthesis.

## What It Does

```
Input: Founder name + company (or CSV batch)
    │
    ├── Exa.ai → Semantic search for articles, blogs, podcasts
    ├── YouTube Data API → Video appearances, interviews, keynotes
    ├── Google Custom Search → Press mentions, media coverage
    ├── Jina Reader → Full content extraction from URLs
    ├── Phantombuster → LinkedIn profile + activity (optional)
    └── Listen Notes / Podcast Index → Podcast appearances (optional)
    │
    ├── LLM relevance filtering (GPT-4o-mini)
    └── LLM profile synthesis (GPT-4o or Claude Sonnet)
    │
    ▼
Output: Structured Markdown profile + JSON cache
```

## Architecture

```
founders-graph/
├── scripts/
│   ├── scrapers/
│   │   ├── apis/
│   │   │   ├── founder_scraper.py      # Unified scraper (orchestrates all sources)
│   │   │   ├── exa.py                  # Exa.ai semantic search client
│   │   │   ├── jina.py                 # Jina URL-to-Markdown reader
│   │   │   ├── youtube.py              # YouTube Data API v3 client
│   │   │   ├── google_search.py        # Google Custom Search client
│   │   │   ├── podcasts.py             # Listen Notes + Podcast Index clients
│   │   │   └── content_scraper.py      # Exa + Jina combined pipeline
│   │   └── linkedin/
│   │       └── phantombuster.py        # LinkedIn scraper via Phantombuster API
│   ├── parsers/
│   │   ├── models.py                   # Pydantic data models (FounderProfile, Position, etc.)
│   │   └── linkedin_parser.py          # Parse LinkedIn .md exports into FounderProfile
│   ├── enrichment/
│   │   ├── enrichment_pipeline.py      # Main enrichment orchestrator
│   │   └── relevance_filter.py         # LLM-based content relevance scoring
│   ├── synthesis/
│   │   └── llm_synthesizer.py          # LLM profile generation (OpenAI or Anthropic)
│   └── batch_scrape.py                 # CSV batch processing with resume support
├── data/
│   ├── input/                          # Input data (Phantombuster JSON exports)
│   ├── cache/                          # Raw JSON outputs from scrapers
│   ├── output/                         # Generated Markdown profiles
│   └── enriched/                       # LLM-enriched profiles
├── requirements.txt
└── .env.example
```

## API Clients

| Client | API | Purpose | Auth |
|--------|-----|---------|------|
| `exa.py` | Exa.ai | Semantic search for founder content (auto-excludes social media, categorizes results) | API key |
| `jina.py` | Jina Reader | Convert any URL to clean Markdown (title, content, word count, author, date) | Optional API key |
| `youtube.py` | YouTube Data API v3 | Find video appearances (4 search queries: interview, podcast, talk, general) | API key |
| `google_search.py` | Google Custom Search | Find press mentions, articles, interviews (excludes social media, categorizes) | API key + CSE ID |
| `podcasts.py` | Listen Notes / Podcast Index | Find podcast episodes (guest, host, mentioned) | API key |
| `phantombuster.py` | Phantombuster | Scrape LinkedIn profiles and activity | API key |

## Enrichment Pipeline

The full enrichment pipeline (`enrichment_pipeline.py`) takes a LinkedIn Markdown profile and enriches it:

1. **Parse** LinkedIn .md file → FounderProfile (Pydantic)
2. **Scrape** full LinkedIn profile via Phantombuster
3. **Scrape** LinkedIn activity (posts)
4. **Search** YouTube for video appearances
5. **Search** Google for media coverage
6. **Search** podcast appearances (Listen Notes)
7. **Filter** results via LLM relevance scoring (GPT-4o-mini, scores 0-100)
8. **Synthesize** enriched Markdown profile via LLM (GPT-4o or Claude Sonnet)

### Relevance Filter

LLM-based scoring for each search result:
- 90-100: Direct interview/podcast appearance
- 70-89: Content created by the person
- 50-69: Significant mention
- Below 50: Filtered out

### LLM Synthesis

Supports two providers (falls back automatically):
- OpenAI (GPT-4o) — primary
- Anthropic (Claude Sonnet) — fallback

Generates structured Markdown with: executive summary, current position, professional journey, education, expertise, media appearances, LinkedIn activity, contact info.

## Batch Processing

Process a CSV of founders:

```bash
python scripts/batch_scrape.py /path/to/founders.csv --max=5 --start=0
```

**CSV format:** `firstName`, `lastName`, `companyName`

Features:
- Skips already-generated profiles
- Resumable with `--start=N`
- macOS notifications every 10 founders
- Progress tracking with ETA
- 1-second delay between requests

## Data Model

```python
FounderProfile
├── id, name                           # Identity
├── current_position: Position         # Title, company, duration
├── location, industry                 # Demographics
├── summary, role_description          # Bio
├── linkedin_url                       # LinkedIn
├── experiences: list[Position]        # Career history
├── education: list[Education]         # Schools, degrees
├── skills: list[str]                  # Skill tags
├── linkedin_posts: list[Activity]     # Posts with engagement metrics
├── media_mentions: list[MediaMention] # Press mentions
├── video_appearances: list[Video]     # YouTube/podcast appearances
├── executive_summary: str             # LLM-generated
├── expertise_areas: list[str]         # LLM-generated
└── enriched_at, sources_used          # Metadata
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env.local
# Edit .env.local with your API keys
```

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `EXA_API_KEY` | Yes | Exa.ai semantic search |
| `YOUTUBE_API_KEY` | Yes | YouTube video search |
| `GOOGLE_API_KEY` | Yes | Google Custom Search |
| `GOOGLE_SEARCH_ENGINE_ID` | Yes | Google CSE ID |
| `OPENAI_API_KEY` | Yes | LLM synthesis + relevance filtering |
| `JINA_API_KEY` | No | Jina Reader (works without, with limits) |
| `ANTHROPIC_API_KEY` | No | Alternative LLM provider |
| `PHANTOMBUSTER_API_KEY` | No | LinkedIn scraping |
| `LISTENNOTES_API_KEY` | No | Podcast search |

### API Rate Limits

| API | Free Tier |
|-----|-----------|
| Exa.ai | 1,000 req/month |
| Jina Reader | 1M credits/month |
| YouTube Data | 10,000 req/day |
| Google Custom Search | 100 req/day |
| Phantombuster | Paid only |

## Usage

```bash
# Single founder
python -m scripts.scrapers.apis.founder_scraper "Sam Altman" "OpenAI" --max=5

# Batch from CSV
python scripts/batch_scrape.py founders.csv --max=5

# Full enrichment (from LinkedIn .md)
python -m scripts.enrichment.enrichment_pipeline input.md output.md
```

## Output

Each founder generates a Markdown profile:

```markdown
# Founder Name
*Company Name*

## Summary
| Source | Results |
|--------|---------|
| Articles & Blogs | 5 |
| YouTube Videos | 10 |
| Press Mentions | 8 |

## Articles & Blog Posts
[Links, dates, categories]

## Full Content (Scraped)
[Full article text, word counts]

## YouTube Videos
[Titles, channels, dates]

## Press & Mentions
[Press results]
```

Plus a JSON cache file: `data/cache/{name}_raw.json`
