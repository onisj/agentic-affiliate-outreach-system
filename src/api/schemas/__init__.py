"""
API Schemas Package

This package contains Pydantic models for request/response validation and serialization.

Modules:
    campaigns: Campaign-related schemas
    content: Content-related schemas
    prospect: Prospect-related schemas
    sequence: Sequence-related schemas
    template: Template-related schemas
"""

from .campaigns import (
    CampaignStatus,
    CampaignCreate,
    CampaignResponse,
    CampaignBase,
)

from .content import (
    ContentCreate,
    ContentResponse,
)

from .prospect import (
    ProspectStatusEnum,
    ProspectCreate,
    ProspectUpdate,
    ProspectResponse,
)

from .sequence import (
    SequenceBase,
    SequenceCreate,
    SequenceUpdate,
    SequenceResponse,
)

from .template import (
    MessageTypeEnum,
    TemplateCreate,
    TemplateResponse,
)
