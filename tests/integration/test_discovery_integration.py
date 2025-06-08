"""
Discovery Module Integration Tests

This module contains integration tests for the discovery components.
"""

import pytest
from datetime import datetime, timedelta
from services.discovery import (
    AIAgent,
    LinkedInScraper,
    DataCleaner,
    DataValidator,
    DataEnricher,
    ProspectScorer,
    SmartScheduler,
    TaskManager
)
from services.monitoring import MonitoringService

@pytest.fixture
async def discovery_components():
    """Initialize discovery components for testing."""
    monitoring = MonitoringService()
    config = {
        "monitoring": monitoring,
        "max_concurrent_tasks": 5,
        "task_timeout": 300,
        "retry_attempts": 3,
        "retry_delay": 5
    }
    
    return {
        "ai_agent": AIAgent(config),
        "scraper": LinkedInScraper(config),
        "cleaner": DataCleaner(config),
        "validator": DataValidator(config),
        "enricher": DataEnricher(config),
        "scorer": ProspectScorer(config),
        "scheduler": SmartScheduler(config),
        "task_manager": TaskManager(config)
    }

@pytest.mark.asyncio
async def test_discovery_pipeline(discovery_components):
    """Test the complete discovery pipeline."""
    # Test data
    profile_url = "https://linkedin.com/in/test-profile"
    
    try:
        # 1. Schedule scraping task
        task_id = await discovery_components["scheduler"].schedule_task(
            task_type="scrape",
            platform="linkedin",
            target=profile_url
        )
        
        # 2. Wait for task completion
        task_status = await discovery_components["task_manager"].get_task_status(task_id)
        assert task_status["status"] == "completed"
        
        # 3. Get scraped data
        raw_data = await discovery_components["task_manager"].get_task_result(task_id)
        assert raw_data is not None
        
        # 4. Clean data
        cleaned_data = await discovery_components["cleaner"].clean(raw_data)
        assert cleaned_data is not None
        
        # 5. Validate data
        validation_result = await discovery_components["validator"].validate(cleaned_data)
        assert validation_result["is_valid"]
        
        # 6. Enrich data
        enriched_data = await discovery_components["enricher"].enrich(cleaned_data)
        assert enriched_data is not None
        
        # 7. Score prospect
        score = await discovery_components["scorer"].score(enriched_data)
        assert score is not None
        
        # 8. Analyze with AI
        analysis = await discovery_components["ai_agent"].analyze(enriched_data)
        assert analysis is not None
        
    except Exception as e:
        pytest.fail(f"Discovery pipeline test failed: {str(e)}")

@pytest.mark.asyncio
async def test_scheduler_task_management(discovery_components):
    """Test scheduler task management."""
    try:
        # Schedule multiple tasks
        task_ids = []
        for i in range(3):
            task_id = await discovery_components["scheduler"].schedule_task(
                task_type="scrape",
                platform="linkedin",
                target=f"https://linkedin.com/in/test-profile-{i}"
            )
            task_ids.append(task_id)
            
        # Check task status
        for task_id in task_ids:
            status = await discovery_components["task_manager"].get_task_status(task_id)
            assert status is not None
            
        # Get queue status
        queue_status = await discovery_components["scheduler"].get_queue_status()
        assert queue_status is not None
        
    except Exception as e:
        pytest.fail(f"Scheduler task management test failed: {str(e)}")

@pytest.mark.asyncio
async def test_data_processing_pipeline(discovery_components):
    """Test data processing pipeline."""
    # Test data
    test_data = {
        "profile_url": "https://linkedin.com/in/test-profile",
        "name": "Test User",
        "title": "Software Engineer",
        "company": "Test Company",
        "location": "Test Location",
        "connections": 500,
        "skills": ["Python", "JavaScript", "React"],
        "experience": [
            {
                "title": "Software Engineer",
                "company": "Test Company",
                "duration": "2 years"
            }
        ]
    }
    
    try:
        # 1. Clean data
        cleaned_data = await discovery_components["cleaner"].clean(test_data)
        assert cleaned_data is not None
        
        # 2. Validate data
        validation_result = await discovery_components["validator"].validate(cleaned_data)
        assert validation_result["is_valid"]
        
        # 3. Enrich data
        enriched_data = await discovery_components["enricher"].enrich(cleaned_data)
        assert enriched_data is not None
        
        # 4. Score prospect
        score = await discovery_components["scorer"].score(enriched_data)
        assert score is not None
        
    except Exception as e:
        pytest.fail(f"Data processing pipeline test failed: {str(e)}")

@pytest.mark.asyncio
async def test_error_handling(discovery_components):
    """Test error handling in discovery components."""
    try:
        # Test invalid profile URL
        with pytest.raises(Exception):
            await discovery_components["scraper"].scrape_profile("invalid-url")
            
        # Test invalid data
        with pytest.raises(Exception):
            await discovery_components["cleaner"].clean(None)
            
        # Test invalid task
        with pytest.raises(Exception):
            await discovery_components["scheduler"].schedule_task(
                task_type="invalid",
                platform="linkedin",
                target="test"
            )
            
    except Exception as e:
        pytest.fail(f"Error handling test failed: {str(e)}") 