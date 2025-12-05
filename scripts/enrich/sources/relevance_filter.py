"""
LLM-based relevance filter for media content search results.
Uses OpenAI to verify and categorize search results.
"""
import os
import json
from pathlib import Path
from typing import Optional
from openai import OpenAI

# Load env
env_file = Path(__file__).parent.parent.parent.parent / ".env.local"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())


class RelevanceFilter:
    """
    LLM-based filter to verify relevance of search results.
    Uses GPT-4o-mini for cost efficiency.
    """

    CATEGORIES = [
        "interview",      # Interview sur une autre chaîne/podcast
        "own_content",    # Contenu créé par la personne (sa chaîne)
        "podcast",        # Apparition podcast
        "talk",           # Conférence, keynote, présentation
        "mention",        # Mentionné dans le contenu
        "article",        # Article écrit par ou sur la personne
        "irrelevant"      # Non pertinent (contenu perso, homonyme, etc.)
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY required for relevance filtering")

        self.client = OpenAI(api_key=self.api_key)

    def filter_results(
        self,
        person_name: str,
        person_context: str,
        results: list[dict],
        min_relevance_score: int = 50
    ) -> list[dict]:
        """
        Filter and categorize search results using LLM.

        Args:
            person_name: Full name of the person
            person_context: Brief description (job title, company, domain)
            results: List of search results with 'title', 'description', 'url', etc.
            min_relevance_score: Minimum score (0-100) to keep a result

        Returns:
            Filtered list with added 'relevance_score' and 'category' fields
        """
        if not results:
            return []

        # Prepare results for LLM
        results_text = self._format_results_for_prompt(results)

        prompt = f"""Tu es un assistant qui évalue la pertinence de résultats de recherche pour un profil professionnel.

PERSONNE RECHERCHÉE:
- Nom: {person_name}
- Contexte: {person_context}

RÉSULTATS À ÉVALUER:
{results_text}

Pour chaque résultat, détermine:
1. relevance_score (0-100): Pertinence pour le profil PROFESSIONNEL de cette personne
   - 90-100: Interview directe, podcast où la personne est invitée, talk/conférence
   - 70-89: Contenu créé par la personne (sa chaîne YouTube, son blog)
   - 50-69: Mention significative dans un contenu pertinent
   - 20-49: Mention légère ou contexte peu clair
   - 0-19: Non pertinent (homonyme, contenu personnel non-pro, spam)

2. category: Une des catégories suivantes:
   - "interview": Interview sur une autre chaîne/média
   - "own_content": Contenu créé par la personne
   - "podcast": Apparition dans un podcast
   - "talk": Conférence, keynote, présentation
   - "mention": Mentionné dans le contenu
   - "article": Article écrit par ou sur la personne
   - "irrelevant": Non pertinent

3. reason: Courte explication (max 10 mots)

Réponds UNIQUEMENT en JSON valide avec ce format:
{{
  "evaluations": [
    {{"index": 0, "relevance_score": 85, "category": "interview", "reason": "Interview directe sur chaîne tech"}},
    {{"index": 1, "relevance_score": 15, "category": "irrelevant", "reason": "Vidéo personnelle non professionnelle"}}
  ]
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Tu réponds uniquement en JSON valide."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            content = response.choices[0].message.content.strip()
            # Clean potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            evaluations = json.loads(content)["evaluations"]

            # Merge evaluations with original results
            filtered_results = []
            for eval_item in evaluations:
                idx = eval_item["index"]
                if idx < len(results):
                    result = results[idx].copy()
                    result["relevance_score"] = eval_item["relevance_score"]
                    result["category"] = eval_item["category"]
                    result["relevance_reason"] = eval_item.get("reason", "")

                    if result["relevance_score"] >= min_relevance_score:
                        filtered_results.append(result)

            # Sort by relevance score
            filtered_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            return filtered_results

        except Exception as e:
            print(f"  [!] LLM filtering error: {e}")
            # Fallback: return all results without filtering
            return results

    def _format_results_for_prompt(self, results: list[dict]) -> str:
        """Format results list for LLM prompt."""
        lines = []
        for i, r in enumerate(results):
            title = r.get("title", "N/A")
            desc = r.get("description", "")[:200] if r.get("description") else "N/A"
            channel = r.get("channel_title") or r.get("source") or "N/A"
            url = r.get("url", "N/A")

            lines.append(f"[{i}] Titre: {title}")
            lines.append(f"    Source/Chaîne: {channel}")
            lines.append(f"    Description: {desc}")
            lines.append(f"    URL: {url}")
            lines.append("")

        return "\n".join(lines)

    def quick_filter(
        self,
        person_name: str,
        results: list[dict],
        content_type: str = "video"
    ) -> list[dict]:
        """
        Quick filter with minimal context.

        Args:
            person_name: Name of the person
            results: Search results
            content_type: "video", "article", or "podcast"
        """
        context = f"Recherche de contenu {content_type} professionnel"
        return self.filter_results(person_name, context, results)


# Quick test
if __name__ == "__main__":
    # Test data
    test_results = [
        {
            "title": "What does a Solutions Architect (SA) do? - iLyas Bakouch",
            "description": "Interview with iLyas Bakouch about Solutions Architecture",
            "channel_title": "Eric Tech",
            "url": "https://youtube.com/watch?v=123"
        },
        {
            "title": "Rumba sur une terrasse",
            "description": "",
            "channel_title": "iLyas Bakouch",
            "url": "https://youtube.com/watch?v=456"
        },
        {
            "title": "AWS Solutions Architect - AMA Live Session",
            "description": "Join me in this live AMA session about Solutions Architecture",
            "channel_title": "Win The cloud 🙌🏻",
            "url": "https://youtube.com/watch?v=789"
        }
    ]

    filter = RelevanceFilter()
    print("Testing relevance filter on sample results...")

    filtered = filter.filter_results(
        person_name="iLyas Bakouch",
        person_context="Cloud Strategist, Founder of Win The Cloud, AWS Solutions Architect",
        results=test_results,
        min_relevance_score=40
    )

    print(f"\nFiltered results ({len(filtered)}/{len(test_results)} kept):\n")
    for r in filtered:
        print(f"  [{r['relevance_score']}] {r['category'].upper()}")
        print(f"      {r['title']}")
        print(f"      Reason: {r.get('relevance_reason', 'N/A')}")
        print()
