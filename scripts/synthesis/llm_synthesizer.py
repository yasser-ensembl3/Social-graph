"""
LLM-powered synthesizer to generate enriched founder profiles.
"""
import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

# Load env
env_file = Path(__file__).parent.parent.parent / ".env.local"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.parsers.models import FounderProfile


class ProfileSynthesizer:
    """Synthesizes enriched data into a comprehensive founder profile."""

    SYSTEM_PROMPT = """Tu es un expert en création de profils de founders.
À partir des données collectées (LinkedIn, articles, vidéos, mentions presse),
génère un profil Markdown complet et professionnel.

Ton output doit être:
- Factuel et basé sur les données fournies
- Bien structuré avec des sections claires
- En français
- Professionnel mais engageant

Ne fabrique pas d'informations. Si une donnée manque, omets la section."""

    def __init__(self, model: Optional[str] = None):
        self.llm_provider = None
        self.llm_client = None

        openai_key = os.environ.get("OPENAI_API_KEY")
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

        if openai_key and HAS_OPENAI:
            self.llm_provider = "openai"
            self.llm_client = openai.OpenAI(api_key=openai_key)
            self.model = model or "gpt-4o"
        elif anthropic_key and HAS_ANTHROPIC:
            self.llm_provider = "anthropic"
            self.llm_client = anthropic.Anthropic(api_key=anthropic_key)
            self.model = model or "claude-sonnet-4-20250514"
        else:
            raise ValueError("OPENAI_API_KEY ou ANTHROPIC_API_KEY requis")

    def synthesize(self, profile: FounderProfile, enriched_data: dict) -> str:
        """Generate enriched Markdown profile from all collected data."""

        # Build context from all sources
        context = f"""
# Données collectées pour {profile.name}

## Profil LinkedIn de base
- Nom: {profile.name}
- Titre: {profile.current_position.title if profile.current_position else 'N/A'}
- Entreprise: {profile.current_position.company if profile.current_position else 'N/A'}
- Localisation: {profile.location}
- Industrie: {profile.industry}
- Résumé: {profile.summary}
- Description du rôle: {profile.role_description}

## Données enrichies LinkedIn
{json.dumps(enriched_data.get('linkedin_full', {}), indent=2, ensure_ascii=False)}

## Posts LinkedIn
{json.dumps(enriched_data.get('linkedin_posts', []), indent=2, ensure_ascii=False)}

## Résultats Google Search
{json.dumps(enriched_data.get('google_results', []), indent=2, ensure_ascii=False)}

## Vidéos YouTube
{json.dumps(enriched_data.get('youtube_results', []), indent=2, ensure_ascii=False)}
"""

        prompt = f"""{context}

---

Génère un profil Markdown enrichi et complet pour ce founder.

Structure attendue:
```markdown
# [Nom]

## Résumé exécutif
[3-4 phrases percutantes résumant qui est cette personne]

## Position actuelle
[Détails sur le rôle actuel]

## Parcours professionnel
[Historique des expériences]

## Formation
[Si disponible]

## Expertises clés
[Liste des domaines d'expertise]

## Présence en ligne

### Articles & Publications
[Si trouvés]

### Podcasts & Conférences
[Si trouvés]

### Activité LinkedIn
[Posts notables si disponibles]

## Dans les médias
[Mentions presse si trouvées]

## Informations de contact
- LinkedIn: [url]
- Localisation: [ville]
```

Génère uniquement le Markdown, sans commentaires."""

        if self.llm_provider == "openai":
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            return response.choices[0].message.content

        elif self.llm_provider == "anthropic":
            response = self.llm_client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text


def generate_enriched_profile(profile: FounderProfile, enriched_data: dict, output_path: Path):
    """Generate and save enriched profile markdown."""
    synthesizer = ProfileSynthesizer()
    markdown = synthesizer.synthesize(profile, enriched_data)

    output_path.write_text(markdown, encoding='utf-8')
    print(f"Generated: {output_path}")

    return markdown
