"""
Parser for LinkedIn profile .md files.
"""
import re
from pathlib import Path
from typing import Optional
from .models import FounderProfile, Position


def slugify(name: str) -> str:
    """Create URL-safe ID from name."""
    import unicodedata
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')
    name = name.lower().strip()
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name)
    return name


def parse_linkedin_md(file_path: Path) -> FounderProfile:
    """Parse a LinkedIn .md file into a FounderProfile."""
    content = file_path.read_text(encoding='utf-8')

    # Extract name from H1
    name_match = re.search(r'^#\s*[^\w]*\s*(.+)$', content, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else file_path.stem

    # Clean emoji from name
    name = re.sub(r'[^\w\s\-\.]', '', name).strip()

    profile = FounderProfile(
        id=slugify(name),
        name=name
    )

    # Parse Position actuelle
    title_match = re.search(r'\*\*Titre\*\*\s*:\s*(.+)', content)
    company_match = re.search(r'\*\*Entreprise\*\*\s*:\s*(.+)', content)
    duration_role_match = re.search(r'\*\*Durée dans le rôle\*\*\s*:\s*(.+)', content)
    duration_company_match = re.search(r'\*\*Durée dans l\'entreprise\*\*\s*:\s*(.+)', content)

    if title_match or company_match:
        profile.current_position = Position(
            title=title_match.group(1).strip() if title_match else None,
            company=company_match.group(1).strip() if company_match else None,
            duration_role=duration_role_match.group(1).strip() if duration_role_match else None,
            duration_company=duration_company_match.group(1).strip() if duration_company_match else None
        )

    # Parse Location & Industry
    location_match = re.search(r'\*\*Localisation\*\*\s*:\s*(.+)', content)
    industry_match = re.search(r'\*\*Industrie\*\*\s*:\s*(.+)', content)

    profile.location = location_match.group(1).strip() if location_match else None
    profile.industry = industry_match.group(1).strip() if industry_match else None

    # Parse Role Description
    desc_section = re.search(r'## Description du rôle\s*\n\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
    profile.role_description = desc_section.group(1).strip() if desc_section else None

    # Parse Summary
    summary_section = re.search(r'## Résumé\s*\n\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
    profile.summary = summary_section.group(1).strip() if summary_section else None

    # Parse Connection info
    degree_match = re.search(r'\*\*Degré de connexion\*\*\s*:\s*(.+)', content)
    linkedin_match = re.search(r'\*\*Profil LinkedIn\*\*\s*:\s*(.+)', content)
    shared_match = re.search(r'\*\*Connexions partagées\*\*\s*:\s*(\d+)', content)

    profile.connection_degree = degree_match.group(1).strip() if degree_match else None
    profile.linkedin_url = linkedin_match.group(1).strip() if linkedin_match else None
    profile.shared_connections = int(shared_match.group(1)) if shared_match else None

    return profile


def parse_all_profiles(directory: Path) -> list[FounderProfile]:
    """Parse all .md files in a directory."""
    profiles = []
    for md_file in directory.glob('*.md'):
        try:
            profile = parse_linkedin_md(md_file)
            profiles.append(profile)
        except Exception as e:
            print(f"Error parsing {md_file}: {e}")
    return profiles


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python linkedin_parser.py <file_or_directory>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if path.is_file():
        profile = parse_linkedin_md(path)
        print(json.dumps(profile.model_dump(), indent=2, default=str))
    else:
        profiles = parse_all_profiles(path)
        print(f"Parsed {len(profiles)} profiles")
        for p in profiles[:3]:
            print(f"  - {p.name} @ {p.current_position.company if p.current_position else 'N/A'}")
