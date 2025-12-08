# Founders Graph

Scraper unifié pour collecter des informations sur des founders à partir de multiples sources (articles, blogs, podcasts, vidéos YouTube, mentions presse).

## Architecture

```
founders-graph/
├── scripts/
│   ├── scrapers/
│   │   ├── apis/                    # APIs publiques
│   │   │   ├── founder_scraper.py   # Scraper unifié (combine tout)
│   │   │   ├── exa.py               # Exa.ai - Recherche sémantique
│   │   │   ├── jina.py              # Jina Reader - Extraction contenu
│   │   │   ├── youtube.py           # YouTube Data API
│   │   │   ├── google_search.py     # Google Custom Search
│   │   │   ├── podcasts.py          # Listen Notes API
│   │   │   └── content_scraper.py   # Exa + Jina combiné
│   │   │
│   │   └── linkedin/                # LinkedIn scraping
│   │       └── phantombuster.py     # Phantombuster API
│   │
│   ├── parsers/                     # Parsers de données
│   │   ├── linkedin_parser.py       # Parse profils LinkedIn (.md)
│   │   └── models.py                # Modèles de données
│   │
│   ├── enrichment/                  # Pipeline d'enrichissement
│   │   ├── enrichment_pipeline.py   # Pipeline principal
│   │   └── relevance_filter.py      # Filtre LLM de pertinence
│   │
│   ├── synthesis/                   # Génération de profils
│   │   └── llm_synthesizer.py       # Synthèse via LLM
│   │
│   └── batch_scrape.py              # Script batch pour CSV
│
├── data/
│   ├── input/                       # Données d'entrée
│   ├── cache/                       # Cache et données intermédiaires
│   └── output/                      # Profils .md générés
│
├── .env.local                       # Variables d'environnement (API keys)
├── .env.example                     # Template des variables
└── requirements.txt                 # Dépendances Python
```

## Scrapers disponibles

### 1. Founder Scraper (Unifié)

**Fichier:** `scripts/scrapers/apis/founder_scraper.py`

Combine toutes les sources en un seul appel et génère un fichier Markdown complet.

```bash
python3 -m scripts.scrapers.apis.founder_scraper "Nom Founder" "Company" --max=5
```

**Sources utilisées:**
- Exa.ai (recherche sémantique)
- Jina Reader (extraction contenu)
- YouTube Data API
- Google Custom Search

**Output:** `data/output/nom-founder.md`

---

### 2. Exa.ai Client

**Fichier:** `scripts/scrapers/apis/exa.py`

Recherche sémantique d'articles, blogs et podcasts.

```python
from scripts.scrapers.apis.exa import ExaClient

client = ExaClient()
results = client.search_founder_content("Sam Altman", "OpenAI", num_results=10)
```

**Features:**
- Recherche par nom + company
- Exclut automatiquement LinkedIn, Facebook, Twitter
- Catégorise les résultats (blog, article, podcast, video)

---

### 3. Jina Reader

**Fichier:** `scripts/scrapers/apis/jina.py`

Convertit n'importe quelle URL en Markdown propre.

```python
from scripts.scrapers.apis.jina import JinaReader

reader = JinaReader()
content = reader.read_url("https://example.com/article")
# Retourne: {title, content, word_count, ...}
```

**Features:**
- Extraction de contenu propre
- Gère JavaScript
- 1M crédits gratuits/mois

---

### 4. YouTube Client

**Fichier:** `scripts/scrapers/apis/youtube.py`

Recherche de vidéos YouTube mentionnant un founder.

```python
from scripts.scrapers.apis.youtube import YouTubeClient

client = YouTubeClient()
results = client.search_person_content("Elon Musk", max_results=10)
```

---

### 5. Google Custom Search

**Fichier:** `scripts/scrapers/apis/google_search.py`

Recherche de mentions presse, interviews, articles.

```python
from scripts.scrapers.apis.google_search import GoogleSearchClient

client = GoogleSearchClient()
results = client.search_media_appearances("Naval Ravikant", "AngelList")
```

**Features:**
- Exclut automatiquement les réseaux sociaux
- Catégorise par type (podcast, interview, article, etc.)

---

### 6. Phantombuster (LinkedIn)

**Fichier:** `scripts/scrapers/linkedin/phantombuster.py`

Scrape les profils LinkedIn via Phantombuster.

```python
from scripts.scrapers.linkedin.phantombuster import PhantombusterClient

client = PhantombusterClient()
profile = client.scrape_linkedin_profile("https://linkedin.com/in/username")
```

---

## Batch Scraping

Pour scraper une liste de founders depuis un CSV:

```bash
python3 scripts/batch_scrape.py "/path/to/founders.csv" --max=5
```

**Features:**
- Notification macOS tous les 10 founders
- Skip automatique si déjà scrapé
- Reprise possible avec `--start=N`

**Format CSV attendu:**
- Colonne `firstName`: Prénom
- Colonne `lastName`: Nom
- Colonne `companyName`: Entreprise

---

## Configuration

### Variables d'environnement

Créer un fichier `.env.local` à la racine:

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

# OpenAI (pour synthèse LLM)
OPENAI_API_KEY=your_openai_key

# Phantombuster (optionnel)
PHANTOMBUSTER_API_KEY=your_pb_key
```

### APIs et limites

| API | Coût | Limite gratuite |
|-----|------|-----------------|
| Exa.ai | $1/1000 req | 1000 req/mois |
| Jina Reader | Gratuit | 1M crédits/mois |
| YouTube Data | Gratuit | 10,000 req/jour |
| Google Custom Search | $5/1000 req | 100 req/jour |
| Phantombuster | Payant | - |

---

## Installation

```bash
# Cloner le repo
git clone https://github.com/your-username/founders-graph.git
cd founders-graph

# Installer les dépendances
pip install -r requirements.txt

# Configurer les API keys
cp .env.example .env.local
# Éditer .env.local avec vos clés

# Tester
python3 -m scripts.scrapers.apis.founder_scraper "Test Founder" --max=2
```

---

## Output

Chaque founder génère un fichier Markdown structuré:

```markdown
# Nom Founder
*Company*

## 📊 Summary
| Source | Results |
|--------|---------|
| Articles & Blogs (Exa) | 5 |
| YouTube Videos | 10 |
| Press & Mentions (Google) | 8 |

## 📚 Articles & Blog Posts
[Liste des articles trouvés]

## 📖 Full Content (Scraped)
[Contenu complet extrait par Jina]

## 🎬 YouTube Videos
[Liste des vidéos]

## 🔎 Press & Mentions
[Mentions presse]
```

---

## License

MIT
