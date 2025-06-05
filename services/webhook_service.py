from typing import Dict, Any, List, Optional
import logging
import hmac
import hashlib
import json
import aiohttp
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from database.models import Webhook, WebhookDelivery, WebhookEventType, MessageStatus, ProspectStatus, CampaignStatus
from uuid import UUID
import time
from ratelimit import limits, sleep_and_retry
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
import statistics
from concurrent.futures import ThreadPoolExecutor
import random
import numpy as np

logger = logging.getLogger(__name__)

# Rate limiting configuration
MAX_CALLS_PER_MINUTE = 60
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds

# Event payload schemas
class MessageEventPayload(BaseModel):
    message_id: str
    prospect_id: str
    campaign_id: Optional[str]
    timestamp: datetime
    external_message_id: Optional[str]

class MessageOpenedPayload(MessageEventPayload):
    opened_at: datetime
    device_info: Optional[Dict[str, Any]]
    location: Optional[Dict[str, Any]]

class MessageClickedPayload(MessageEventPayload):
    clicked_at: datetime
    click_url: str
    click_type: str  # e.g., "link", "button", "image"
    click_position: Optional[Dict[str, int]]  # x, y coordinates

class MessageRepliedPayload(MessageEventPayload):
    replied_at: datetime
    reply_analysis: Dict[str, Any]
    reply_content: str
    reply_metadata: Optional[Dict[str, Any]]

class ProspectStatusPayload(BaseModel):
    prospect_id: str
    old_status: str
    new_status: str
    changed_at: datetime
    triggered_by: str
    metadata: Optional[Dict[str, Any]]

class CampaignStatusPayload(BaseModel):
    campaign_id: str
    old_status: str
    new_status: str
    changed_at: datetime
    metrics: Optional[Dict[str, Any]]

class MessageBouncedPayload(MessageEventPayload):
    bounced_at: datetime
    bounce_type: str  # e.g., "hard", "soft"
    bounce_reason: str
    bounce_details: Optional[Dict[str, Any]]

class MessageFailedPayload(MessageEventPayload):
    failed_at: datetime
    failure_reason: str
    failure_details: Optional[Dict[str, Any]]

class ProspectEngagementPayload(BaseModel):
    prospect_id: str
    engagement_type: str  # e.g., "website_visit", "form_submit", "content_view"
    timestamp: datetime
    engagement_data: Dict[str, Any]

# Event schema mapping
EVENT_SCHEMAS = {
    WebhookEventType.MESSAGE_OPENED: MessageOpenedPayload,
    WebhookEventType.MESSAGE_CLICKED: MessageClickedPayload,
    WebhookEventType.MESSAGE_REPLIED: MessageRepliedPayload,
    WebhookEventType.PROSPECT_STATUS_CHANGED: ProspectStatusPayload,
    WebhookEventType.CAMPAIGN_STATUS_CHANGED: CampaignStatusPayload,
    WebhookEventType.MESSAGE_BOUNCED: MessageBouncedPayload,
    WebhookEventType.MESSAGE_FAILED: MessageFailedPayload,
    WebhookEventType.PROSPECT_ENGAGEMENT: ProspectEngagementPayload
}

class LoadTestConfig(BaseModel):
    """Configuration for load testing."""
    duration_seconds: int = Field(60, ge=1, le=3600)  # 1 second to 1 hour
    requests_per_second: int = Field(10, ge=1, le=1000)
    concurrent_requests: int = Field(5, ge=1, le=100)
    event_types: List[WebhookEventType]
    payload_variation: bool = Field(True, description="Whether to vary payloads")

class LoadTestResult(BaseModel):
    """Results of a load test."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_distribution: Dict[str, int]
    event_type_distribution: Dict[str, int]
    response_time_distribution: List[float]
    start_time: datetime
    end_time: datetime

class ConcurrentTestConfig(BaseModel):
    """Configuration for concurrent testing."""
    total_requests: int = Field(100, ge=1, le=10000)
    concurrent_requests: int = Field(10, ge=1, le=100)
    event_types: List[WebhookEventType]
    delay_between_batches: float = Field(0.1, ge=0, le=10)  # seconds

class ConcurrentTestResult(BaseModel):
    """Results of a concurrent test."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_distribution: Dict[str, int]
    event_type_distribution: Dict[str, int]
    response_time_distribution: List[float]
    start_time: datetime
    end_time: datetime
    batch_results: List[Dict[str, Any]]

class StressTestConfig(BaseModel):
    """Configuration for stress testing."""
    duration_seconds: int = Field(300, ge=60, le=3600)  # 1 minute to 1 hour
    initial_rps: int = Field(10, ge=1, le=100)
    max_rps: int = Field(1000, ge=1, le=10000)
    step_duration_seconds: int = Field(30, ge=10, le=300)
    rps_increment: int = Field(10, ge=1, le=100)
    concurrent_requests: int = Field(5, ge=1, le=100)
    event_types: List[WebhookEventType]
    failure_threshold: float = Field(0.1, ge=0, le=1)  # Stop if failure rate exceeds this

class StressTestResult(BaseModel):
    """Results of a stress test."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    max_sustainable_rps: int
    failure_threshold_reached: bool
    step_results: List[Dict[str, Any]]
    error_distribution: Dict[str, int]
    event_type_distribution: Dict[str, int]
    response_time_distribution: List[float]
    start_time: datetime
    end_time: datetime

class SpikeTestConfig(BaseModel):
    """Configuration for spike testing."""
    duration_seconds: int = Field(60, ge=10, le=300)  # 10 seconds to 5 minutes
    spike_rps: int = Field(1000, ge=100, le=10000)
    pre_spike_rps: int = Field(10, ge=1, le=100)
    post_spike_rps: int = Field(10, ge=1, le=100)
    spike_duration_seconds: int = Field(10, ge=1, le=60)
    concurrent_requests: int = Field(5, ge=1, le=100)
    event_types: List[WebhookEventType]
    recovery_time_threshold: float = Field(5.0, ge=1, le=60)  # Maximum acceptable recovery time in seconds

class SpikeTestResult(BaseModel):
    """Results of a spike test."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    spike_success_rate: float
    recovery_time: float
    pre_spike_metrics: Dict[str, Any]
    spike_metrics: Dict[str, Any]
    post_spike_metrics: Dict[str, Any]
    error_distribution: Dict[str, int]
    event_type_distribution: Dict[str, int]
    response_time_distribution: List[float]
    start_time: datetime
    end_time: datetime

class WebhookService:
    """Service for managing webhooks and their deliveries."""
    
    def __init__(self, db: Session):
        self.db = db
        self._rate_limiters = {}  # Store rate limiters per webhook
        self._delivery_queue = asyncio.Queue()  # Queue for webhook deliveries
    
    def _get_rate_limiter(self, webhook_id: str):
        """Get or create a rate limiter for a webhook."""
        if webhook_id not in self._rate_limiters:
            @sleep_and_retry
            @limits(calls=MAX_CALLS_PER_MINUTE, period=60)
            def rate_limited_call(*args, **kwargs):
                return True
            self._rate_limiters[webhook_id] = rate_limited_call
        return self._rate_limiters[webhook_id]
    
    async def start_delivery_worker(self):
        """Start the webhook delivery worker."""
        while True:
            try:
                delivery_task = await self._delivery_queue.get()
                await self._process_delivery_task(delivery_task)
                self._delivery_queue.task_done()
            except Exception as e:
                logger.error(f"Error in delivery worker: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on errors
    
    async def _process_delivery_task(self, task: Dict[str, Any]):
        """Process a webhook delivery task from the queue."""
        webhook = task["webhook"]
        event_type = task["event_type"]
        payload = task["payload"]
        
        await self._deliver_webhook_with_retry(webhook, event_type, payload)
    
    def _validate_payload(self, event_type: WebhookEventType, payload: Dict[str, Any]) -> bool:
        """Validate webhook payload against schema."""
        try:
            schema = EVENT_SCHEMAS.get(event_type)
            if not schema:
                logger.warning(f"No schema defined for event type: {event_type}")
                return True  # Allow unknown event types
            
            # Convert datetime strings to datetime objects if needed
            if "timestamp" in payload and isinstance(payload["timestamp"], str):
                payload["timestamp"] = datetime.fromisoformat(payload["timestamp"])
            
            # Validate payload
            schema(**payload)
            return True
        except Exception as e:
            logger.error(f"Payload validation failed: {e}")
            return False
    
    async def create_webhook(
        self,
        url: str,
        events: List[WebhookEventType],
        description: Optional[str] = None,
        validate_payloads: bool = True
    ) -> Dict[str, Any]:
        """Create a new webhook configuration."""
        try:
            # Generate a random secret for HMAC signing
            secret = hashlib.sha256(str(UUID.uuid4()).encode()).hexdigest()
            
            webhook = Webhook(
                url=url,
                secret=secret,
                events=events,
                description=description,
                validate_payloads=validate_payloads
            )
            
            self.db.add(webhook)
            self.db.commit()
            
            return {
                "success": True,
                "webhook": {
                    "id": str(webhook.id),
                    "url": webhook.url,
                    "events": webhook.events,
                    "secret": webhook.secret,  # Only returned once during creation
                    "validate_payloads": validate_payloads
                }
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating webhook: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    async def _deliver_webhook_with_retry(
        self,
        webhook: Webhook,
        event_type: WebhookEventType,
        payload: Dict[str, Any],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Deliver a webhook with exponential backoff retry logic."""
        try:
            # Apply rate limiting
            rate_limiter = self._get_rate_limiter(str(webhook.id))
            rate_limiter()
            
            # Prepare payload
            payload_str = json.dumps(payload)
            signature = self._generate_signature(payload_str, webhook.secret)
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-Event": event_type,
                "X-Webhook-Delivery-ID": str(UUID.uuid4())
            }
            
            # Create delivery record
            delivery = WebhookDelivery(
                webhook_id=webhook.id,
                event_type=event_type,
                payload=payload,
                retry_count=retry_count
            )
            self.db.add(delivery)
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook.url,
                    headers=headers,
                    data=payload_str,
                    timeout=10
                ) as response:
                    delivery.response_code = response.status
                    delivery.response_body = await response.text()
                    delivery.success = 200 <= response.status < 300
                    
                    if not delivery.success:
                        delivery.error_message = f"HTTP {response.status}: {delivery.response_body}"
                        webhook.failure_count += 1
                        
                        # Retry logic with exponential backoff
                        if retry_count < MAX_RETRIES:
                            retry_delay = INITIAL_RETRY_DELAY * (2 ** retry_count)
                            logger.info(f"Retrying webhook delivery in {retry_delay} seconds...")
                            await asyncio.sleep(retry_delay)
                            return await self._deliver_webhook_with_retry(
                                webhook, event_type, payload, retry_count + 1
                            )
                    else:
                        webhook.failure_count = 0
                    
                    webhook.last_triggered_at = datetime.now(timezone.utc)
                    self.db.commit()
                    
                    return {
                        "success": delivery.success,
                        "status_code": response.status,
                        "delivery_id": str(delivery.id),
                        "retry_count": retry_count
                    }
                    
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error delivering webhook: {e}")
            
            # Retry on network errors
            if retry_count < MAX_RETRIES:
                retry_delay = INITIAL_RETRY_DELAY * (2 ** retry_count)
                logger.info(f"Retrying webhook delivery in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                return await self._deliver_webhook_with_retry(
                    webhook, event_type, payload, retry_count + 1
                )
            
            return {"success": False, "error": str(e)}
    
    async def trigger_webhook(
        self,
        event_type: WebhookEventType,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger webhooks for a specific event."""
        try:
            # Find active webhooks for this event
            webhooks = self.db.query(Webhook).filter(
                Webhook.is_active == True,
                Webhook.events.contains([event_type])
            ).all()
            
            if not webhooks:
                return {"success": True, "message": "No webhooks configured for this event"}
            
            # Queue deliveries for all matching webhooks
            results = []
            for webhook in webhooks:
                # Validate payload if required
                if webhook.validate_payloads and not self._validate_payload(event_type, payload):
                    results.append({
                        "webhook_id": str(webhook.id),
                        "url": webhook.url,
                        "success": False,
                        "error": "Payload validation failed"
                    })
                    continue
                
                # Queue the delivery
                await self._delivery_queue.put({
                    "webhook": webhook,
                    "event_type": event_type,
                    "payload": payload
                })
                
                results.append({
                    "webhook_id": str(webhook.id),
                    "url": webhook.url,
                    "success": True,
                    "queued": True
                })
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error triggering webhooks: {e}")
            return {"success": False, "error": str(e)}
    
    async def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: str
    ) -> bool:
        """Verify the HMAC signature of an incoming webhook."""
        try:
            expected_signature = self._generate_signature(payload, secret)
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    async def get_webhook_deliveries(
        self,
        webhook_id: Optional[str] = None,
        event_type: Optional[WebhookEventType] = None,
        success: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get webhook delivery history with optional filters."""
        try:
            query = self.db.query(WebhookDelivery)
            
            if webhook_id:
                query = query.filter(WebhookDelivery.webhook_id == webhook_id)
            if event_type:
                query = query.filter(WebhookDelivery.event_type == event_type)
            if success is not None:
                query = query.filter(WebhookDelivery.success == success)
            
            deliveries = query.order_by(
                WebhookDelivery.created_at.desc()
            ).limit(limit).all()
            
            return [{
                "id": str(d.id),
                "webhook_id": str(d.webhook_id),
                "event_type": d.event_type,
                "success": d.success,
                "response_code": d.response_code,
                "created_at": d.created_at.isoformat(),
                "error_message": d.error_message
            } for d in deliveries]
            
        except Exception as e:
            logger.error(f"Error getting webhook deliveries: {e}")
            return []
    
    async def get_webhook_stats(
        self,
        webhook_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get webhook delivery statistics."""
        try:
            query = self.db.query(WebhookDelivery)
            
            if webhook_id:
                query = query.filter(WebhookDelivery.webhook_id == webhook_id)
            if start_date:
                query = query.filter(WebhookDelivery.created_at >= start_date)
            if end_date:
                query = query.filter(WebhookDelivery.created_at <= end_date)
            
            total_deliveries = query.count()
            successful_deliveries = query.filter(WebhookDelivery.success == True).count()
            failed_deliveries = query.filter(WebhookDelivery.success == False).count()
            
            # Get average response time
            response_times = query.filter(
                WebhookDelivery.response_code.isnot(None)
            ).with_entities(
                func.extract('epoch', WebhookDelivery.updated_at - WebhookDelivery.created_at)
            ).all()
            
            avg_response_time = sum(t[0] for t in response_times) / len(response_times) if response_times else 0
            
            # Get retry statistics
            retry_stats = query.with_entities(
                WebhookDelivery.retry_count,
                func.count(WebhookDelivery.id)
            ).group_by(WebhookDelivery.retry_count).all()
            
            return {
                "total_deliveries": total_deliveries,
                "successful_deliveries": successful_deliveries,
                "failed_deliveries": failed_deliveries,
                "success_rate": (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0,
                "avg_response_time": avg_response_time,
                "retry_stats": {str(r[0]): r[1] for r in retry_stats}
            }
            
        except Exception as e:
            logger.error(f"Error getting webhook stats: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_test_payload(self, event_type: WebhookEventType) -> Dict[str, Any]:
        """Generate a realistic test payload for the given event type."""
        base_payload = {
            "message_id": str(UUID.uuid4()),
            "prospect_id": str(UUID.uuid4()),
            "campaign_id": str(UUID.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "external_message_id": f"test_{int(time.time())}"
        }
        
        if event_type == WebhookEventType.MESSAGE_OPENED:
            return {
                **base_payload,
                "opened_at": datetime.now(timezone.utc).isoformat(),
                "device_info": {
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    "platform": "macOS",
                    "browser": "Chrome"
                },
                "location": {
                    "country": "US",
                    "city": "San Francisco",
                    "timezone": "America/Los_Angeles"
                }
            }
        elif event_type == WebhookEventType.MESSAGE_CLICKED:
            return {
                **base_payload,
                "clicked_at": datetime.now(timezone.utc).isoformat(),
                "click_url": "https://example.com/test",
                "click_type": "link",
                "click_position": {"x": 100, "y": 200}
            }
        elif event_type == WebhookEventType.MESSAGE_REPLIED:
            return {
                **base_payload,
                "replied_at": datetime.now(timezone.utc).isoformat(),
                "reply_content": "I'm interested in learning more about your program!",
                "reply_analysis": {
                    "sentiment": 0.8,
                    "is_positive": True,
                    "is_negative": False,
                    "contains_questions": True,
                    "contains_contact": True,
                    "intent": "interest"
                },
                "reply_metadata": {
                    "channel": "email",
                    "response_time": 3600  # seconds
                }
            }
        elif event_type == WebhookEventType.PROSPECT_STATUS_CHANGED:
            return {
                "prospect_id": str(UUID.uuid4()),
                "old_status": ProspectStatus.NEW,
                "new_status": ProspectStatus.INTERESTED,
                "changed_at": datetime.now(timezone.utc).isoformat(),
                "triggered_by": "message_reply",
                "metadata": {
                    "message_id": str(UUID.uuid4()),
                    "campaign_id": str(UUID.uuid4())
                }
            }
        elif event_type == WebhookEventType.CAMPAIGN_STATUS_CHANGED:
            return {
                "campaign_id": str(UUID.uuid4()),
                "old_status": CampaignStatus.DRAFT,
                "new_status": CampaignStatus.ACTIVE,
                "changed_at": datetime.now(timezone.utc).isoformat(),
                "metrics": {
                    "total_prospects": 100,
                    "messages_sent": 50,
                    "open_rate": 0.45,
                    "click_rate": 0.25
                }
            }
        elif event_type == WebhookEventType.MESSAGE_BOUNCED:
            return {
                **base_payload,
                "bounced_at": datetime.now(timezone.utc).isoformat(),
                "bounce_type": "hard",
                "bounce_reason": "invalid_email",
                "bounce_details": {
                    "error_code": "550",
                    "error_message": "No such user here"
                }
            }
        elif event_type == WebhookEventType.MESSAGE_FAILED:
            return {
                **base_payload,
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "failure_reason": "rate_limit_exceeded",
                "failure_details": {
                    "provider": "linkedin",
                    "retry_after": 3600
                }
            }
        elif event_type == WebhookEventType.PROSPECT_ENGAGEMENT:
            return {
                "prospect_id": str(UUID.uuid4()),
                "engagement_type": "website_visit",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "engagement_data": {
                    "page_url": "https://example.com/affiliate-program",
                    "duration": 300,
                    "referrer": "https://google.com",
                    "utm_source": "email",
                    "utm_campaign": "affiliate_outreach"
                }
            }
        
        return base_payload

    async def run_load_test(
        self,
        webhook: Webhook,
        config: LoadTestConfig
    ) -> LoadTestResult:
        """Run a load test on a webhook."""
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(seconds=config.duration_seconds)
        
        response_times = []
        error_distribution = {}
        event_type_distribution = {}
        successful_requests = 0
        failed_requests = 0
        
        async def make_request():
            event_type = random.choice(config.event_types)
            payload = await self.generate_test_payload(event_type)
            
            if config.payload_variation:
                # Add some random variation to the payload
                payload["timestamp"] = datetime.now(timezone.utc).isoformat()
                if "metadata" in payload:
                    payload["metadata"]["test_id"] = str(UUID.uuid4())
            
            start_time = time.time()
            try:
                result = await self._deliver_webhook_with_retry(
                    webhook=webhook,
                    event_type=event_type,
                    payload=payload
                )
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if result["success"]:
                    successful_requests += 1
                else:
                    failed_requests += 1
                    error_type = result.get("error", "Unknown error")
                    error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
                
                event_type_distribution[event_type] = event_type_distribution.get(event_type, 0) + 1
                
            except Exception as e:
                failed_requests += 1
                error_type = str(e)
                error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
        
        # Calculate delay between requests
        delay = 1.0 / config.requests_per_second
        
        # Create semaphore for concurrent requests
        semaphore = asyncio.Semaphore(config.concurrent_requests)
        
        async def bounded_request():
            async with semaphore:
                await make_request()
        
        # Run the load test
        while datetime.now(timezone.utc) < end_time:
            tasks = [bounded_request() for _ in range(config.concurrent_requests)]
            await asyncio.gather(*tasks)
            await asyncio.sleep(delay)
        
        # Calculate statistics
        total_requests = successful_requests + failed_requests
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0
        
        return LoadTestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            error_distribution=error_distribution,
            event_type_distribution=event_type_distribution,
            response_time_distribution=response_times,
            start_time=start_time,
            end_time=datetime.now(timezone.utc)
        )
    
    async def run_concurrent_test(
        self,
        webhook: Webhook,
        config: ConcurrentTestConfig
    ) -> ConcurrentTestResult:
        """Run a concurrent test on a webhook."""
        start_time = datetime.now(timezone.utc)
        
        response_times = []
        error_distribution = {}
        event_type_distribution = {}
        successful_requests = 0
        failed_requests = 0
        batch_results = []
        
        # Calculate number of batches
        num_batches = (config.total_requests + config.concurrent_requests - 1) // config.concurrent_requests
        
        for batch in range(num_batches):
            batch_start_time = time.time()
            batch_successful = 0
            batch_failed = 0
            batch_response_times = []
            
            # Create tasks for this batch
            tasks = []
            for _ in range(min(config.concurrent_requests, config.total_requests - batch * config.concurrent_requests)):
                event_type = random.choice(config.event_types)
                payload = await self.generate_test_payload(event_type)
                
                async def make_request():
                    nonlocal batch_successful, batch_failed
                    start_time = time.time()
                    try:
                        result = await self._deliver_webhook_with_retry(
                            webhook=webhook,
                            event_type=event_type,
                            payload=payload
                        )
                        
                        response_time = time.time() - start_time
                        batch_response_times.append(response_time)
                        response_times.append(response_time)
                        
                        if result["success"]:
                            batch_successful += 1
                            successful_requests += 1
                        else:
                            batch_failed += 1
                            failed_requests += 1
                            error_type = result.get("error", "Unknown error")
                            error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
                        
                        event_type_distribution[event_type] = event_type_distribution.get(event_type, 0) + 1
                        
                    except Exception as e:
                        batch_failed += 1
                        failed_requests += 1
                        error_type = str(e)
                        error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
                
                tasks.append(make_request())
            
            # Run the batch
            await asyncio.gather(*tasks)
            
            # Record batch results
            batch_duration = time.time() - batch_start_time
            batch_results.append({
                "batch_number": batch + 1,
                "successful_requests": batch_successful,
                "failed_requests": batch_failed,
                "avg_response_time": statistics.mean(batch_response_times) if batch_response_times else 0,
                "duration": batch_duration
            })
            
            # Wait between batches if not the last batch
            if batch < num_batches - 1:
                await asyncio.sleep(config.delay_between_batches)
        
        # Calculate statistics
        total_requests = successful_requests + failed_requests
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0
        
        return ConcurrentTestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            error_distribution=error_distribution,
            event_type_distribution=event_type_distribution,
            response_time_distribution=response_times,
            start_time=start_time,
            end_time=datetime.now(timezone.utc),
            batch_results=batch_results
        )
    
    async def run_stress_test(
        self,
        webhook: Webhook,
        config: StressTestConfig
    ) -> StressTestResult:
        """Run a stress test on a webhook to find its breaking point."""
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(seconds=config.duration_seconds)
        
        current_rps = config.initial_rps
        step_results = []
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []
        error_distribution = {}
        event_type_distribution = {}
        failure_threshold_reached = False
        
        while datetime.now(timezone.utc) < end_time and not failure_threshold_reached:
            step_start_time = time.time()
            step_requests = 0
            step_successful = 0
            step_failed = 0
            step_response_times = []
            
            # Calculate requests for this step
            requests_this_step = current_rps * config.step_duration_seconds
            
            # Create semaphore for concurrent requests
            semaphore = asyncio.Semaphore(config.concurrent_requests)
            
            async def make_request():
                nonlocal step_requests, step_successful, step_failed
                event_type = random.choice(config.event_types)
                payload = await self.generate_test_payload(event_type)
                payload["test_type"] = "stress"
                payload["test_id"] = str(UUID.uuid4())
                payload["rps"] = current_rps
                
                start_time = time.time()
                try:
                    result = await self._deliver_webhook_with_retry(
                        webhook=webhook,
                        event_type=event_type,
                        payload=payload
                    )
                    
                    response_time = time.time() - start_time
                    step_response_times.append(response_time)
                    response_times.append(response_time)
                    
                    if result["success"]:
                        step_successful += 1
                        successful_requests += 1
                    else:
                        step_failed += 1
                        failed_requests += 1
                        error_type = result.get("error", "Unknown error")
                        error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
                    
                    event_type_distribution[event_type] = event_type_distribution.get(event_type, 0) + 1
                    
                except Exception as e:
                    step_failed += 1
                    failed_requests += 1
                    error_type = str(e)
                    error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
            
            async def bounded_request():
                async with semaphore:
                    await make_request()
            
            # Run the step
            while step_requests < requests_this_step and not failure_threshold_reached:
                tasks = [bounded_request() for _ in range(min(config.concurrent_requests, requests_this_step - step_requests))]
                await asyncio.gather(*tasks)
                step_requests += len(tasks)
                
                # Check failure threshold
                if step_requests > 0:
                    failure_rate = step_failed / step_requests
                    if failure_rate > config.failure_threshold:
                        failure_threshold_reached = True
                        break
            
            # Record step results
            step_duration = time.time() - step_start_time
            step_results.append({
                "rps": current_rps,
                "total_requests": step_requests,
                "successful_requests": step_successful,
                "failed_requests": step_failed,
                "failure_rate": step_failed / step_requests if step_requests > 0 else 0,
                "avg_response_time": statistics.mean(step_response_times) if step_response_times else 0,
                "duration": step_duration
            })
            
            # Increment RPS if not at max and failure threshold not reached
            if not failure_threshold_reached and current_rps < config.max_rps:
                current_rps += config.rps_increment
            
            total_requests += step_requests
        
        return StressTestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            max_sustainable_rps=current_rps - config.rps_increment if failure_threshold_reached else current_rps,
            failure_threshold_reached=failure_threshold_reached,
            step_results=step_results,
            error_distribution=error_distribution,
            event_type_distribution=event_type_distribution,
            response_time_distribution=response_times,
            start_time=start_time,
            end_time=datetime.now(timezone.utc)
        )
    
    async def run_spike_test(
        self,
        webhook: Webhook,
        config: SpikeTestConfig
    ) -> SpikeTestResult:
        """Run a spike test on a webhook to test its behavior under sudden load."""
        start_time = datetime.now(timezone.utc)
        
        # Initialize metrics
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []
        error_distribution = {}
        event_type_distribution = {}
        
        # Helper function to run a phase of the test
        async def run_phase(rps: int, duration: int, phase_name: str) -> Dict[str, Any]:
            phase_start_time = time.time()
            phase_requests = 0
            phase_successful = 0
            phase_failed = 0
            phase_response_times = []
            
            # Calculate total requests for this phase
            total_phase_requests = rps * duration
            
            # Create semaphore for concurrent requests
            semaphore = asyncio.Semaphore(config.concurrent_requests)
            
            async def make_request():
                nonlocal phase_requests, phase_successful, phase_failed
                event_type = random.choice(config.event_types)
                payload = await self.generate_test_payload(event_type)
                payload["test_type"] = "spike"
                payload["test_id"] = str(UUID.uuid4())
                payload["phase"] = phase_name
                payload["rps"] = rps
                
                start_time = time.time()
                try:
                    result = await self._deliver_webhook_with_retry(
                        webhook=webhook,
                        event_type=event_type,
                        payload=payload
                    )
                    
                    response_time = time.time() - start_time
                    phase_response_times.append(response_time)
                    response_times.append(response_time)
                    
                    if result["success"]:
                        phase_successful += 1
                        successful_requests += 1
                    else:
                        phase_failed += 1
                        failed_requests += 1
                        error_type = result.get("error", "Unknown error")
                        error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
                    
                    event_type_distribution[event_type] = event_type_distribution.get(event_type, 0) + 1
                    
                except Exception as e:
                    phase_failed += 1
                    failed_requests += 1
                    error_type = str(e)
                    error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
            
            async def bounded_request():
                async with semaphore:
                    await make_request()
            
            # Run the phase
            while phase_requests < total_phase_requests:
                tasks = [bounded_request() for _ in range(min(config.concurrent_requests, total_phase_requests - phase_requests))]
                await asyncio.gather(*tasks)
                phase_requests += len(tasks)
                await asyncio.sleep(1.0 / rps)  # Maintain RPS
            
            phase_duration = time.time() - phase_start_time
            return {
                "phase": phase_name,
                "rps": rps,
                "total_requests": phase_requests,
                "successful_requests": phase_successful,
                "failed_requests": phase_failed,
                "success_rate": phase_successful / phase_requests if phase_requests > 0 else 0,
                "avg_response_time": statistics.mean(phase_response_times) if phase_response_times else 0,
                "duration": phase_duration
            }
        
        # Run pre-spike phase
        pre_spike_metrics = await run_phase(config.pre_spike_rps, 10, "pre_spike")
        
        # Run spike phase
        spike_metrics = await run_phase(config.spike_rps, config.spike_duration_seconds, "spike")
        
        # Run post-spike phase and measure recovery time
        post_spike_start = time.time()
        post_spike_metrics = await run_phase(config.post_spike_rps, 30, "post_spike")
        recovery_time = time.time() - post_spike_start
        
        # Calculate spike success rate
        spike_success_rate = spike_metrics["success_rate"]
        
        return SpikeTestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            spike_success_rate=spike_success_rate,
            recovery_time=recovery_time,
            pre_spike_metrics=pre_spike_metrics,
            spike_metrics=spike_metrics,
            post_spike_metrics=post_spike_metrics,
            error_distribution=error_distribution,
            event_type_distribution=event_type_distribution,
            response_time_distribution=response_times,
            start_time=start_time,
            end_time=datetime.now(timezone.utc)
        ) 