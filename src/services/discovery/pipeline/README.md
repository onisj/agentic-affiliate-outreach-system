# Discovery Pipeline

The Discovery Pipeline is a crucial component of the Agentic Affiliate Outreach System, responsible for processing and analyzing data collected from various social media platforms and websites. It transforms raw scraped data into actionable insights for affiliate discovery and scoring.

## Pipeline Components

### 1. Data Cleaner (`data_cleaner.py`)
- Cleans and normalizes raw data from scrapers
- Handles text normalization, HTML cleaning, and data type conversion
- Ensures consistent data format across different platforms
- Implements robust error handling and logging

### 2. Data Validator (`data_validator.py`)
- Validates cleaned data against predefined schemas
- Ensures data integrity and completeness
- Performs format validation for emails, URLs, and other fields
- Provides detailed validation reports with errors and warnings

### 3. Data Enricher (`data_enricher.py`)
- Enhances data with additional insights and analysis
- Performs sentiment analysis on content
- Extracts entities and topics
- Analyzes engagement patterns and network structure
- Infers demographics and interests

### 4. Prospect Scorer (`prospect_scorer.py`)
- Implements multi-dimensional scoring for prospects
- Evaluates audience quality, content relevance, and influence
- Calculates conversion potential and engagement propensity
- Provides weighted composite scores for ranking

## Data Flow

```
[Scrapers] -> [Data Cleaner] -> [Data Validator] -> [Data Enricher] -> [Prospect Scorer]
```

1. **Scrapers** (`adapters/*_scraper.py`)
   - Collect raw data from different platforms
   - Return standardized `DataObject` instances

2. **Data Cleaner**
   - Normalizes and standardizes raw data
   - Handles platform-specific data formats
   - Ensures consistent data structure

3. **Data Validator**
   - Validates data against schemas
   - Ensures data quality and completeness
   - Flags potential issues

4. **Data Enricher**
   - Adds derived insights and analysis
   - Enhances data with AI-powered features
   - Provides deeper understanding of prospects

5. **Prospect Scorer**
   - Evaluates prospects across multiple dimensions
   - Generates actionable scores
   - Ranks prospects for outreach

## Integration with Intelligence Components

The pipeline works closely with the intelligence components (`intelligence/*_analysis.py`):

- **Profile Analysis**: Uses enriched data for detailed profile analysis
- **Trend Analysis**: Processes cleaned data to identify trends
- **Network Analysis**: Analyzes enriched network data
- **Competitive Analysis**: Uses scored data for competitive intelligence

## Usage

```python
from services.discovery.pipeline import DiscoveryPipeline

# Initialize pipeline
pipeline = DiscoveryPipeline(config)

# Process single profile
result = await pipeline.process_profile(profile_data)

# Process batch of profiles
results = await pipeline.process_batch(profiles)
```

## Configuration

The pipeline components can be configured through the `config` dictionary:

```python
config = {
    'cleaning': {
        'text_normalization': True,
        'html_cleaning': True
    },
    'validation': {
        'strict_mode': True,
        'schema_version': '1.0'
    },
    'enrichment': {
        'sentiment_analysis': True,
        'entity_extraction': True
    },
    'scoring': {
        'weights': {
            'audience_quality': 0.25,
            'content_relevance': 0.25,
            'influence_level': 0.20,
            'conversion_potential': 0.15,
            'engagement_propensity': 0.15
        }
    }
}
```

## Error Handling

The pipeline implements comprehensive error handling:

- Each component logs errors using `MonitoringService`
- Failed validations are reported with detailed messages
- Processing continues for batch operations even if individual items fail
- Errors are propagated with context for debugging

## Monitoring

All pipeline components use the `MonitoringService` for:

- Performance tracking
- Error logging
- Rate limit monitoring
- Data quality metrics

## Best Practices

1. Always validate data before enrichment
2. Use appropriate error handling for each stage
3. Monitor pipeline performance and data quality
4. Regularly update scoring weights based on results
5. Keep schemas and validation rules up to date 