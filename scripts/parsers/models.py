"""
Pydantic models for Founder profiles.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Position(BaseModel):
    """Current or past position."""
    title: Optional[str] = None
    company: Optional[str] = None
    duration_role: Optional[str] = None
    duration_company: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class Education(BaseModel):
    """Education entry."""
    school: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    dates: Optional[str] = None


class LinkedInActivity(BaseModel):
    """LinkedIn post or article."""
    type: str  # post, article
    content: Optional[str] = None
    date: Optional[str] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    url: Optional[str] = None


class MediaMention(BaseModel):
    """Press or media mention."""
    title: str
    source: Optional[str] = None
    url: Optional[str] = None
    date: Optional[str] = None
    snippet: Optional[str] = None


class VideoAppearance(BaseModel):
    """YouTube/podcast appearance."""
    title: str
    channel: Optional[str] = None
    url: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None


class FounderProfile(BaseModel):
    """Complete founder profile."""
    # Identity
    id: str
    name: str

    # Current position
    current_position: Optional[Position] = None

    # Location & Industry
    location: Optional[str] = None
    industry: Optional[str] = None

    # Bio
    summary: Optional[str] = None
    role_description: Optional[str] = None

    # LinkedIn
    linkedin_url: Optional[str] = None
    connection_degree: Optional[str] = None
    shared_connections: Optional[int] = None

    # Enriched data
    experiences: list[Position] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)

    # Activity & Content
    linkedin_posts: list[LinkedInActivity] = Field(default_factory=list)
    media_mentions: list[MediaMention] = Field(default_factory=list)
    video_appearances: list[VideoAppearance] = Field(default_factory=list)

    # LLM-generated
    executive_summary: Optional[str] = None
    expertise_areas: list[str] = Field(default_factory=list)

    # Metadata
    enriched_at: Optional[datetime] = None
    sources_used: list[str] = Field(default_factory=list)
