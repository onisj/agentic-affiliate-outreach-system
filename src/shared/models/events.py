"""
Event Sourcing Models

This module implements the event sourcing patterns for the system,
providing a foundation for CQRS architecture and event-driven communication.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import json

class EventType(Enum):
    """Types of events in the system"""
    # Discovery Events
    PROSPECT_DISCOVERED = "prospect_discovered"
    PROSPECT_SCORED = "prospect_scored"
    PROSPECT_UPDATED = "prospect_updated"
    
    # Campaign Events
    CAMPAIGN_CREATED = "campaign_created"
    CAMPAIGN_STARTED = "campaign_started"
    CAMPAIGN_PAUSED = "campaign_paused"
    CAMPAIGN_COMPLETED = "campaign_completed"
    
    # Message Events
    MESSAGE_SCHEDULED = "message_scheduled"
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_OPENED = "message_opened"
    MESSAGE_CLICKED = "message_clicked"
    MESSAGE_REPLIED = "message_replied"
    MESSAGE_FAILED = "message_failed"
    
    # Response Events
    RESPONSE_RECEIVED = "response_received"
    RESPONSE_CLASSIFIED = "response_classified"
    RESPONSE_PROCESSED = "response_processed"
    
    # AI Agent Events
    AGENT_DECISION_MADE = "agent_decision_made"
    AGENT_ACTION_EXECUTED = "agent_action_executed"
    AGENT_LEARNING_UPDATED = "agent_learning_updated"
    
    # System Events
    SYSTEM_ERROR = "system_error"
    SYSTEM_HEALTH_CHECK = "system_health_check"

@dataclass
class BaseEvent(ABC):
    """Base class for all events in the system"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = field(init=False)
    aggregate_id: str = ""
    aggregate_type: str = ""
    version: int = 1
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'aggregate_id': self.aggregate_id,
            'aggregate_type': self.aggregate_type,
            'version': self.version,
            'timestamp': self.timestamp.isoformat(),
            'data': self.get_event_data(),
            'metadata': self.metadata
        }
    
    @abstractmethod
    def get_event_data(self) -> Dict[str, Any]:
        """Get event-specific data"""
        pass
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEvent':
        """Create event from dictionary"""
        # This would be implemented by each specific event class
        raise NotImplementedError

# Discovery Events
@dataclass
class ProspectDiscoveredEvent(BaseEvent):
    """Event fired when a new prospect is discovered"""
    event_type: EventType = field(default=EventType.PROSPECT_DISCOVERED, init=False)
    
    prospect_id: str = ""
    platform: str = ""
    profile_data: Dict[str, Any] = field(default_factory=dict)
    discovery_criteria: Dict[str, Any] = field(default_factory=dict)
    initial_score: float = 0.0
    
    def get_event_data(self) -> Dict[str, Any]:
        return {
            'prospect_id': self.prospect_id,
            'platform': self.platform,
            'profile_data': self.profile_data,
            'discovery_criteria': self.discovery_criteria,
            'initial_score': self.initial_score
        }

@dataclass
class ProspectScoredEvent(BaseEvent):
    """Event fired when a prospect is scored or re-scored"""
    event_type: EventType = field(default=EventType.PROSPECT_SCORED, init=False)
    
    prospect_id: str = ""
    previous_score: float = 0.0
    new_score: float = 0.0
    scoring_factors: Dict[str, float] = field(default_factory=dict)
    scoring_model_version: str = ""
    
    def get_event_data(self) -> Dict[str, Any]:
        return {
            'prospect_id': self.prospect_id,
            'previous_score': self.previous_score,
            'new_score': self.new_score,
            'scoring_factors': self.scoring_factors,
            'scoring_model_version': self.scoring_model_version
        }

# Campaign Events
@dataclass
class CampaignCreatedEvent(BaseEvent):
    """Event fired when a new campaign is created"""
    event_type: EventType = field(default=EventType.CAMPAIGN_CREATED, init=False)
    
    campaign_id: str = ""
    campaign_name: str = ""
    campaign_type: str = ""
    target_prospects: List[str] = field(default_factory=list)
    sequence_config: Dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    
    def get_event_data(self) -> Dict[str, Any]:
        return {
            'campaign_id': self.campaign_id,
            'campaign_name': self.campaign_name,
            'campaign_type': self.campaign_type,
            'target_prospects': self.target_prospects,
            'sequence_config': self.sequence_config,
            'created_by': self.created_by
        }

@dataclass
class CampaignStartedEvent(BaseEvent):
    """Event fired when a campaign is started"""
    event_type: EventType = field(default=EventType.CAMPAIGN_STARTED, init=False)
    
    campaign_id: str = ""
    started_by: str = ""
    initial_message_count: int = 0
    
    def get_event_data(self) -> Dict[str, Any]:
        return {
            'campaign_id': self.campaign_id,
            'started_by': self.started_by,
            'initial_message_count': self.initial_message_count
        }

# Message Events
@dataclass
class MessageSentEvent(BaseEvent):
    """Event fired when a message is sent"""
    event_type: EventType = field(default=EventType.MESSAGE_SENT, init=False)
    
    message_id: str = ""
    campaign_id: str = ""
    prospect_id: str = ""
    channel: str = ""
    sequence_step: int = 0
    subject: Optional[str] = None
    content_preview: str = ""
    scheduled_time: Optional[datetime] = None
    sent_time: Optional[datetime] = None
    
    def get_event_data(self) -> Dict[str, Any]:
        return {
            'message_id': self.message_id,
            'campaign_id': self.campaign_id,
            'prospect_id': self.prospect_id,
            'channel': self.channel,
            'sequence_step': self.sequence_step,
            'subject': self.subject,
            'content_preview': self.content_preview,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'sent_time': self.sent_time.isoformat() if self.sent_time else None
        }

@dataclass
class ResponseReceivedEvent(BaseEvent):
    """Event fired when a response is received from a prospect"""
    event_type: EventType = field(default=EventType.RESPONSE_RECEIVED, init=False)
    
    response_id: str = ""
    message_id: str = ""
    prospect_id: str = ""
    campaign_id: str = ""
    channel: str = ""
    response_content: str = ""
    response_time: Optional[datetime] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def get_event_data(self) -> Dict[str, Any]:
        return {
            'response_id': self.response_id,
            'message_id': self.message_id,
            'prospect_id': self.prospect_id,
            'campaign_id': self.campaign_id,
            'channel': self.channel,
            'response_content': self.response_content,
            'response_time': self.response_time.isoformat() if self.response_time else None,
            'raw_data': self.raw_data
        }

# AI Agent Events
@dataclass
class AgentDecisionMadeEvent(BaseEvent):
    """Event fired when the AI agent makes a decision"""
    event_type: EventType = field(default=EventType.AGENT_DECISION_MADE, init=False)
    
    decision_id: str = ""
    decision_type: str = ""
    objective: str = ""
    reasoning: str = ""
    confidence_score: float = 0.0
    recommended_actions: List[Dict[str, Any]] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    
    def get_event_data(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'decision_type': self.decision_type,
            'objective': self.objective,
            'reasoning': self.reasoning,
            'confidence_score': self.confidence_score,
            'recommended_actions': self.recommended_actions,
            'context_data': self.context_data
        }

@dataclass
class AgentActionExecutedEvent(BaseEvent):
    """Event fired when the AI agent executes an action"""
    event_type: EventType = field(default=EventType.AGENT_ACTION_EXECUTED, init=False)
    
    decision_id: str = ""
    action_id: str = ""
    action_type: str = ""
    action_parameters: Dict[str, Any] = field(default_factory=dict)
    execution_result: Dict[str, Any] = field(default_factory=dict)
    success: bool = False
    error_message: Optional[str] = None
    
    def get_event_data(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'action_id': self.action_id,
            'action_type': self.action_type,
            'action_parameters': self.action_parameters,
            'execution_result': self.execution_result,
            'success': self.success,
            'error_message': self.error_message
        }

class EventStore:
    """Event store for persisting and retrieving events"""
    
    def __init__(self, storage_backend: Any):
        self.storage = storage_backend
        self.event_handlers: Dict[EventType, List[callable]] = {}
    
    async def append_event(self, event: BaseEvent) -> None:
        """Append an event to the store"""
        # Persist the event
        await self._persist_event(event)
        
        # Publish the event to handlers
        await self._publish_event(event)
    
    async def get_events(
        self, 
        aggregate_id: str, 
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> List[BaseEvent]:
        """Get events for an aggregate"""
        return await self._load_events(aggregate_id, from_version, to_version)
    
    async def get_events_by_type(
        self, 
        event_type: EventType,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None
    ) -> List[BaseEvent]:
        """Get events by type within a time range"""
        return await self._load_events_by_type(event_type, from_timestamp, to_timestamp)
    
    def register_handler(self, event_type: EventType, handler: callable) -> None:
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _persist_event(self, event: BaseEvent) -> None:
        """Persist event to storage"""
        # This would implement the actual storage logic
        # Could be PostgreSQL, EventStore, or other event storage
        pass
    
    async def _publish_event(self, event: BaseEvent) -> None:
        """Publish event to registered handlers"""
        handlers = self.event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                # Log error but don't fail the event publishing
                print(f"Error in event handler: {e}")
    
    async def _load_events(
        self, 
        aggregate_id: str, 
        from_version: int,
        to_version: Optional[int]
    ) -> List[BaseEvent]:
        """Load events from storage"""
        # This would implement the actual loading logic
        return []
    
    async def _load_events_by_type(
        self, 
        event_type: EventType,
        from_timestamp: Optional[datetime],
        to_timestamp: Optional[datetime]
    ) -> List[BaseEvent]:
        """Load events by type from storage"""
        # This would implement the actual loading logic
        return []

class EventBus:
    """Event bus for real-time event distribution"""
    
    def __init__(self):
        self.subscribers: Dict[EventType, List[callable]] = {}
    
    def subscribe(self, event_type: EventType, handler: callable) -> None:
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    async def publish(self, event: BaseEvent) -> None:
        """Publish an event to all subscribers"""
        handlers = self.subscribers.get(event.event_type, [])
        
        # Execute all handlers concurrently
        tasks = [handler(event) for handler in handlers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def unsubscribe(self, event_type: EventType, handler: callable) -> None:
        """Unsubscribe from an event type"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(handler)
            except ValueError:
                pass  # Handler not found

# Event factory for creating events from dictionaries
class EventFactory:
    """Factory for creating events from serialized data"""
    
    _event_classes = {
        EventType.PROSPECT_DISCOVERED: ProspectDiscoveredEvent,
        EventType.PROSPECT_SCORED: ProspectScoredEvent,
        EventType.CAMPAIGN_CREATED: CampaignCreatedEvent,
        EventType.CAMPAIGN_STARTED: CampaignStartedEvent,
        EventType.MESSAGE_SENT: MessageSentEvent,
        EventType.RESPONSE_RECEIVED: ResponseReceivedEvent,
        EventType.AGENT_DECISION_MADE: AgentDecisionMadeEvent,
        EventType.AGENT_ACTION_EXECUTED: AgentActionExecutedEvent,
    }
    
    @classmethod
    def create_event(cls, event_data: Dict[str, Any]) -> BaseEvent:
        """Create an event from serialized data"""
        event_type = EventType(event_data['event_type'])
        event_class = cls._event_classes.get(event_type)
        
        if not event_class:
            raise ValueError(f"Unknown event type: {event_type}")
        
        return event_class.from_dict(event_data)
    
    @classmethod
    def register_event_class(cls, event_type: EventType, event_class: Type[BaseEvent]) -> None:
        """Register a new event class"""
        cls._event_classes[event_type] = event_class
