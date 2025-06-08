"""
Conversation Flow Manager

This module implements the conversation flow management system for the Agentic Affiliate Outreach System.
It manages the state transitions and timing of outreach conversations based on the defined flow diagram.
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from src.services.monitoring import MonitoringService
from src.services.outreach.personalization import IntelligentPersonalizationEngine
from src.services.outreach.timing.timing_optimizer import TimingOptimizer

class ConversationState(Enum):
    """Enumeration of possible conversation states."""
    INITIAL_OUTREACH = "initial_outreach"
    AWAITING_RESPONSE = "awaiting_response"
    FOLLOW_UP_1 = "follow_up_1"
    AWAITING_RESPONSE_2 = "awaiting_response_2"
    FOLLOW_UP_2 = "follow_up_2"
    FINAL_ATTEMPT = "final_attempt"
    POSITIVE_RESPONSE = "positive_response"
    NEGATIVE_RESPONSE = "negative_response"
    NEUTRAL_RESPONSE = "neutral_response"
    NURTURING_SEQUENCE = "nurturing_sequence"
    INFORMATION_SHARING = "information_sharing"
    CLOSED_UNRESPONSIVE = "closed_unresponsive"
    RESPECTFUL_CLOSURE = "respectful_closure"
    ONBOARDING = "onboarding"

class ConversationFlowManager:
    """Manages the flow of outreach conversations."""
    
    def __init__(
        self,
        monitoring_service: MonitoringService,
        personalization_engine: IntelligentPersonalizationEngine,
        timing_optimizer: TimingOptimizer
    ):
        """Initialize the conversation flow manager."""
        self.monitoring_service = monitoring_service
        self.personalization_engine = personalization_engine
        self.timing_optimizer = timing_optimizer
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
        
    async def start_conversation(
        self,
        prospect_id: str,
        initial_message: str,
        channel: str
    ) -> Dict[str, Any]:
        """Start a new conversation with a prospect."""
        try:
            # Generate conversation ID
            conversation_id = f"conv_{prospect_id}_{datetime.now().timestamp()}"
            
            # Initialize conversation state
            conversation = {
                "id": conversation_id,
                "prospect_id": prospect_id,
                "state": ConversationState.INITIAL_OUTREACH,
                "channel": channel,
                "started_at": datetime.now(),
                "last_updated": datetime.now(),
                "messages": [{
                    "type": "outreach",
                    "content": initial_message,
                    "sent_at": datetime.now()
                }],
                "follow_up_count": 0,
                "response_received": False
            }
            
            # Store conversation
            self.active_conversations[conversation_id] = conversation
            
            # Record metrics
            await self.monitoring_service.record_metric(
                "conversation_started",
                {"conversation_id": conversation_id, "channel": channel}
            )
            
            return conversation
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "conversation_start_failed",
                str(e),
                {"prospect_id": prospect_id, "channel": channel}
            )
            raise
    
    async def update_conversation_state(
        self,
        conversation_id: str,
        new_state: ConversationState,
        response_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update the state of a conversation."""
        try:
            conversation = self.active_conversations.get(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Update state
            old_state = conversation["state"]
            conversation["state"] = new_state
            conversation["last_updated"] = datetime.now()
            
            # Handle response data
            if response_data:
                conversation["messages"].append({
                    "type": "response",
                    "content": response_data.get("content"),
                    "sent_at": datetime.now(),
                    "sentiment": response_data.get("sentiment"),
                    "intent": response_data.get("intent")
                })
                conversation["response_received"] = True
            
            # Handle state-specific actions
            await self._handle_state_transition(conversation, old_state, new_state)
            
            # Record metrics
            await self.monitoring_service.record_metric(
                "conversation_state_changed",
                {
                    "conversation_id": conversation_id,
                    "old_state": old_state.value,
                    "new_state": new_state.value
                }
            )
            
            return conversation
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "conversation_state_update_failed",
                str(e),
                {"conversation_id": conversation_id}
            )
            raise
    
    async def check_conversation_timeouts(self) -> List[Dict[str, Any]]:
        """Check for conversations that need state updates based on timeouts."""
        try:
            updated_conversations = []
            current_time = datetime.now()
            
            for conversation in self.active_conversations.values():
                if conversation["response_received"]:
                    continue
                
                time_since_update = current_time - conversation["last_updated"]
                state = conversation["state"]
                
                # Check timeouts based on state
                if state == ConversationState.AWAITING_RESPONSE and time_since_update >= timedelta(days=3):
                    await self.update_conversation_state(
                        conversation["id"],
                        ConversationState.FOLLOW_UP_1
                    )
                    updated_conversations.append(conversation)
                    
                elif state == ConversationState.AWAITING_RESPONSE_2 and time_since_update >= timedelta(days=7):
                    await self.update_conversation_state(
                        conversation["id"],
                        ConversationState.FOLLOW_UP_2
                    )
                    updated_conversations.append(conversation)
                    
                elif state == ConversationState.FINAL_ATTEMPT and time_since_update >= timedelta(days=14):
                    await self.update_conversation_state(
                        conversation["id"],
                        ConversationState.CLOSED_UNRESPONSIVE
                    )
                    updated_conversations.append(conversation)
            
            return updated_conversations
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "conversation_timeout_check_failed",
                str(e)
            )
            raise
    
    async def _handle_state_transition(
        self,
        conversation: Dict[str, Any],
        old_state: ConversationState,
        new_state: ConversationState
    ) -> None:
        """Handle specific actions for state transitions."""
        try:
            if new_state == ConversationState.FOLLOW_UP_1:
                # Generate follow-up message
                follow_up = await self.personalization_engine.generate_follow_up(
                    conversation["prospect_id"],
                    conversation["messages"][-1]["content"]
                )
                conversation["messages"].append({
                    "type": "follow_up",
                    "content": follow_up,
                    "sent_at": datetime.now()
                })
                conversation["follow_up_count"] += 1
                
            elif new_state == ConversationState.NURTURING_SEQUENCE:
                # Start nurturing sequence
                await self.personalization_engine.start_nurturing_sequence(
                    conversation["prospect_id"]
                )
                
            elif new_state == ConversationState.INFORMATION_SHARING:
                # Generate information sharing content
                info_content = await self.personalization_engine.generate_info_content(
                    conversation["prospect_id"],
                    conversation["messages"][-1]["content"]
                )
                conversation["messages"].append({
                    "type": "information",
                    "content": info_content,
                    "sent_at": datetime.now()
                })
                
            elif new_state in [
                ConversationState.CLOSED_UNRESPONSIVE,
                ConversationState.RESPECTFUL_CLOSURE,
                ConversationState.ONBOARDING
            ]:
                # Remove from active conversations
                self.active_conversations.pop(conversation["id"])
                
        except Exception as e:
            await self.monitoring_service.record_error(
                "state_transition_handler_failed",
                str(e),
                {
                    "conversation_id": conversation["id"],
                    "old_state": old_state.value,
                    "new_state": new_state.value
                }
            )
            raise
    
    async def get_conversation_status(self, conversation_id: str) -> Dict[str, Any]:
        """Get the current status of a conversation."""
        try:
            conversation = self.active_conversations.get(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            return {
                "id": conversation["id"],
                "state": conversation["state"].value,
                "started_at": conversation["started_at"],
                "last_updated": conversation["last_updated"],
                "message_count": len(conversation["messages"]),
                "follow_up_count": conversation["follow_up_count"],
                "response_received": conversation["response_received"]
            }
            
        except Exception as e:
            await self.monitoring_service.record_error(
                "conversation_status_check_failed",
                str(e),
                {"conversation_id": conversation_id}
            )
            raise
    
    async def cleanup(self) -> None:
        """Clean up resources and close active conversations."""
        try:
            for conversation in self.active_conversations.values():
                if conversation["state"] not in [
                    ConversationState.CLOSED_UNRESPONSIVE,
                    ConversationState.RESPECTFUL_CLOSURE,
                    ConversationState.ONBOARDING
                ]:
                    await self.update_conversation_state(
                        conversation["id"],
                        ConversationState.CLOSED_UNRESPONSIVE
                    )
                    
        except Exception as e:
            await self.monitoring_service.record_error(
                "conversation_cleanup_failed",
                str(e)
            )
            raise 