# Discovery Module

This module provides comprehensive prospect discovery capabilities for the Agentic Affiliate Outreach System.

## Components

### Intelligence
Located in `intelligence/`, these components provide AI-powered analysis:
- `AIAgent`: Core AI capabilities for prospect analysis
- `TimingAnalyzer`: Analyzes optimal timing for outreach
- `PersonalizationEngine`: Handles message personalization
- `SentimentAnalyzer`: Analyzes prospect sentiment
- `ProspectScorer`: Scores prospects based on various factors

### Scrapers
Located in `scrapers/`, these components handle data collection:
- `BaseScraper`: Base class for all scrapers
- Platform-specific scrapers for LinkedIn, Twitter, YouTube, TikTok, Instagram, Reddit
- `WebScraper`: Generic web scraping capabilities

### Pipeline
Located in `pipeline/`, these components process collected data:
- `DataCleaner`: Cleans and normalizes data
- `DataValidator`: Validates data quality
- `DataEnricher`: Enriches data with additional information
- `ProspectScorer`: Scores prospects based on enriched data

### Orchestrator
Located in `orchestrator/`, these components manage discovery tasks:
- `SmartScheduler`: Schedules and manages scraping tasks
- `TaskManager`: Manages task execution and monitoring

## Usage

```python
from services.discovery import (
    AIAgent,
    LinkedInScraper,
    DataCleaner,
    SmartScheduler
)

# Initialize components
ai_agent = AIAgent(config={...})
scraper = LinkedInScraper(config={...})
cleaner = DataCleaner(config={...})
scheduler = SmartScheduler(config={...})

# Use components
prospect_data = await scraper.scrape_profile(profile_url)
cleaned_data = await cleaner.clean(prospect_data)
analysis = await ai_agent.analyze(cleaned_data)
```

## Integration

The discovery module integrates with:
- Monitoring service for error tracking and metrics
- Analytics service for data analysis
- Outreach module for prospect engagement

## Error Handling

All components implement consistent error handling:
```python
try:
    result = await component.perform_operation()
except Exception as e:
    monitoring.log_error(
        f"Operation failed: {str(e)}",
        error_type="operation_error",
        component="component_name"
    )
    raise
```

## Metrics

Components automatically record metrics:
```python
monitoring.record_metric(
    'operation_duration',
    duration,
    {'operation': 'name'}
)
```

## Contributing

When adding new components:
1. Place them in the appropriate subdirectory
2. Update this README with documentation
3. Add necessary tests
4. Ensure proper error handling and metrics
5. Update the module's `__init__.py` to expose public interfaces 