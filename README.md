# Founders Graph

Unified scraper for collecting information about founders from multiple sources (articles, blogs, podcasts, YouTube videos, press mentions).

## Architecture

```
founders-graph/
├── scripts/
│   ├── scrapers/
│   │   ├── apis/                    # Public APIs
│   │   │   ├── founder_scraper.py   # Unified scraper (combines everything)
│   │   │   ├── exa.py               # Exa.ai - Semantic search
│   │   │   ├── jina.py              # Jina Reader - Content extraction
│   │   │   ├── youtube.py           # YouTube Data API
│   │   │   ├── google_search.py     # Google Custom Search
│   │   │   ├── podcasts.py          # Listen Notes API
│   │   │   └── content_scraper.py   # Exa + Jina combined
│   │   │
│   │   └── linkedin/                # LinkedIn scraping
│   │       └── phantombuster.py     # Phantombuster API
│   │
│   ├── parsers/                     # Data parsers
│   │   ├── linkedin_parser.py       # Parse LinkedIn profiles (.md)
│   │   └── models.py                # Data models
│   │
│   ├── enrichment/                  # Enrichment pipeline
│   │   ├── enrichment_pipeline.py   # Main pipeline
│   │   └── relevance_filter.py      # LLM relevance filter
│   │
│   ├── synthesis/                   # Profile generation
│   │   └── llm_synthesizer.py       # LLM synthesis
│   │
│   └── batch_scrape.py              # Batch script for CSV
│
├── data/
│   ├── input/                       # Input data
│   ├── cache/                       # Cache and intermediate data
│   └── output/                      # Generated .md profiles
│
├── .env.local                       # Environment variables (API keys)
├── .env.example                     # Variables template
└── requirements.txt                 # Python dependencies
```

## Available Scrapers

### 1. Founder Scraper (Unified)

**File:** `scripts/scrapers/apis/founder_scraper.py`

Combines all sources in a single call and generates a complete Markdown file.

```bash
python3 -m scripts.scrapers.apis.founder_scraper "Founder Name" "Company" --max=5
```

**Sources used:**
- Exa.ai (semantic search)
- Jina Reader (content extraction)
- YouTube Data API
- Google Custom Search

**Output:** `data/output/founder-name.md`

---

### 2. Exa.ai Client

**File:** `scripts/scrapers/apis/exa.py`

Semantic search for articles, blogs, and podcasts.

```python
from scripts.scrapers.apis.exa import ExaClient

client = ExaClient()
results = client.search_founder_content("Sam Altman", "OpenAI", num_results=10)
```

**Features:**
- Search by name + company
- Automatically excludes LinkedIn, Facebook, Twitter
- Categorizes results (blog, article, podcast, video)

---

### 3. Jina Reader

**File:** `scripts/scrapers/apis/jina.py`

Converts any URL into clean Markdown.

```python
from scripts.scrapers.apis.jina import JinaReader

reader = JinaReader()
content = reader.read_url("https://example.com/article")
# Returns: {title, content, word_count, ...}
```

**Features:**
- Clean content extraction
- Handles JavaScript
- 1M free credits/month

---

### 4. YouTube Client

**File:** `scripts/scrapers/apis/youtube.py`

Search for YouTube videos mentioning a founder.

```python
from scripts.scrapers.apis.youtube import YouTubeClient

client = YouTubeClient()
results = client.search_person_content("Elon Musk", max_results=10)
```

---

### 5. Google Custom Search

**File:** `scripts/scrapers/apis/google_search.py`

Search for press mentions, interviews, articles.

```python
from scripts.scrapers.apis.google_search import GoogleSearchClient

client = GoogleSearchClient()
results = client.search_media_appearances("Naval Ravikant", "AngelList")
```

**Features:**
- Automatically excludes social media
- Categorizes by type (podcast, interview, article, etc.)

---

### 6. Phantombuster (LinkedIn)

**File:** `scripts/scrapers/linkedin/phantombuster.py`

Scrapes LinkedIn profiles via Phantombuster.

```python
from scripts.scrapers.linkedin.phantombuster import PhantombusterClient

client = PhantombusterClient()
profile = client.scrape_linkedin_profile("https://linkedin.com/in/username")
```

---

## Batch Scraping

To scrape a list of founders from a CSV:

```bash
python3 scripts/batch_scrape.py "/path/to/founders.csv" --max=5
```

**Features:**
- macOS notification every 10 founders
- Automatic skip if already scraped
- Resume possible with `--start=N`

**Expected CSV format:**
- Column `firstName`: First name
- Column `lastName`: Last name
- Column `companyName`: Company

---

## Configuration

### Environment Variables

Create a `.env.local` file at the root:

```env
# Exa.ai
EXA_API_KEY=your_exa_key

# Jina Reader
JINA_API_KEY=your_jina_key

# YouTube Data API
YOUTUBE_API_KEY=your_youtube_key

# Google Custom Search
GOOGLE_API_KEY=your_google_key
GOOGLE_SEARCH_ENGINE_ID=your_cse_id

# OpenAI (for LLM synthesis)
OPENAI_API_KEY=your_openai_key

# Phantombuster (optional)
PHANTOMBUSTER_API_KEY=your_pb_key
```

### APIs and Limits

| API | Cost | Free Tier |
|-----|------|-----------|
| Exa.ai | $1/1000 req | 1000 req/month |
| Jina Reader | Free | 1M credits/month |
| YouTube Data | Free | 10,000 req/day |
| Google Custom Search | $5/1000 req | 100 req/day |
| Phantombuster | Paid | - |

---

## Installation

```bash
# Clone the repo
git clone https://github.com/your-username/founders-graph.git
cd founders-graph

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env.local
# Edit .env.local with your keys

# Test
python3 -m scripts.scrapers.apis.founder_scraper "Test Founder" --max=2
```

---

## Output

Each founder generates a structured Markdown file:

```markdown
# Founder Name
*Company*

## 📊 Summary
| Source | Results |
|--------|---------|
| Articles & Blogs (Exa) | 5 |
| YouTube Videos | 10 |
| Press & Mentions (Google) | 8 |

## 📚 Articles & Blog Posts
[List of found articles]

## 📖 Full Content (Scraped)
[Full content extracted by Jina]

## 🎬 YouTube Videos
[List of videos]

## 🔎 Press & Mentions
[Press mentions]
```

---

## License

MIT