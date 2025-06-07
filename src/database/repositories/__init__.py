"""
Database Repositories Package

This package contains repository implementations for data access.

Modules:
    prospect: Prospect repository
    campaign: Campaign repository
    sequence: Sequence repository
    template: Template repository
    base: Base repository implementation
"""

from .base import BaseRepository
from .prospect import ProspectRepository
from .campaign import CampaignRepository
from .sequence import SequenceRepository
from .template import TemplateRepository

__all__ = [
    'BaseRepository',
    'ProspectRepository',
    'CampaignRepository',
    'SequenceRepository',
    'TemplateRepository'
] 