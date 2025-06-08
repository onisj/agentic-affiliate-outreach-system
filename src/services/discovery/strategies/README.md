# Discovery Strategies

This directory contains strategy implementations for prospect discovery and analysis in the Agentic Affiliate Outreach System.

## Components

### Behavioral Pattern Recognition
The `BehavioralPatternRecognition` class analyzes user behavior patterns to identify potential prospects based on:
- Content activity patterns
- Interaction patterns
- Temporal patterns
- Sentiment patterns
- Network patterns

### Multi-Dimensional Scoring
The `MultiDimensionalScoring` class calculates composite prospect scores considering:
- Engagement metrics
- Influence metrics
- Relevance metrics
- Activity metrics
- Quality metrics

### Competitive Intelligence
The `CompetitiveIntelligence` class analyzes competitors and market trends:
- Competitor analysis
- Market trend analysis
- Market segment analysis
- Opportunity identification

## Usage

### Behavioral Pattern Recognition
```python
from services.discovery.strategies import BehavioralPatternRecognition

# Initialize
behavioral_analysis = BehavioralPatternRecognition(config={
    'interest_threshold': 0.7,
    'influence_threshold': 0.6,
    'engagement_threshold': 0.5
})

# Analyze patterns
patterns = await behavioral_analysis.analyze_behavioral_patterns(
    user_data=user_data,
    platform='linkedin'
)
```

### Multi-Dimensional Scoring
```python
from services.discovery.strategies import MultiDimensionalScoring

# Initialize
scoring = MultiDimensionalScoring(config={
    'dimension_weights': {
        'engagement': 0.3,
        'influence': 0.25,
        'relevance': 0.2,
        'activity': 0.15,
        'quality': 0.1
    }
})

# Calculate score
score = await scoring.calculate_prospect_score(
    prospect_data=prospect_data,
    platform='linkedin'
)
```

### Competitive Intelligence
```python
from services.discovery.strategies import CompetitiveIntelligence

# Initialize
intelligence = CompetitiveIntelligence(config={
    'competitor_threshold': 0.7,
    'trend_threshold': 0.6,
    'market_threshold': 0.5
})

# Analyze landscape
insights = await intelligence.analyze_competitive_landscape(
    market_data=market_data,
    platform='linkedin'
)
```

## Configuration

### Behavioral Pattern Recognition
- `interest_threshold`: Minimum threshold for interest score (default: 0.7)
- `influence_threshold`: Minimum threshold for influence score (default: 0.6)
- `engagement_threshold`: Minimum threshold for engagement score (default: 0.5)
- `clustering_eps`: DBSCAN clustering epsilon (default: 0.3)
- `clustering_min_samples`: Minimum samples for DBSCAN (default: 5)

### Multi-Dimensional Scoring
- `dimension_weights`: Weights for each scoring dimension
- `score_thresholds`: Thresholds for score categories
  - `high`: High score threshold (default: 0.8)
  - `medium`: Medium score threshold (default: 0.5)
  - `low`: Low score threshold (default: 0.3)

### Competitive Intelligence
- `competitor_threshold`: Minimum threshold for competitor identification (default: 0.7)
- `trend_threshold`: Minimum threshold for trend identification (default: 0.6)
- `market_threshold`: Minimum threshold for market segment identification (default: 0.5)
- `n_clusters`: Number of clusters for market segmentation (default: 5)
- `cluster_min_size`: Minimum size for market segments (default: 10)

## Output Formats

### Behavioral Pattern Recognition
```python
{
    'interests': {
        'score': float,
        'primary_interests': List[str],
        'evolution': Dict[str, Any],
        'confidence': float
    },
    'influence': {
        'score': float,
        'influence_areas': List[str],
        'growth': Dict[str, Any],
        'confidence': float
    },
    'engagement': {
        'score': float,
        'patterns': List[Dict[str, Any]],
        'quality': Dict[str, Any],
        'confidence': float
    },
    'clusters': List[Dict[str, Any]],
    'timestamp': str
}
```

### Multi-Dimensional Scoring
```python
{
    'composite_score': float,
    'category': str,
    'dimension_scores': {
        'engagement': float,
        'influence': float,
        'relevance': float,
        'activity': float,
        'quality': float
    },
    'breakdown': {
        'dimensions': Dict[str, Dict[str, Any]],
        'composite_score': float,
        'timestamp': str
    },
    'timestamp': str
}
```

### Competitive Intelligence
```python
{
    'competitors': {
        'competitors': List[Dict[str, Any]],
        'strengths': Dict[str, List[str]],
        'weaknesses': Dict[str, List[str]],
        'position': Dict[str, Any],
        'overall_score': float
    },
    'trends': {
        'trends': List[Dict[str, Any]],
        'impact': Dict[str, Dict[str, float]],
        'evolution': Dict[str, Dict[str, Any]],
        'relevance': Dict[str, float],
        'overall_score': float
    },
    'segments': {
        'segments': List[Dict[str, Any]],
        'characteristics': Dict[str, Dict[str, Any]],
        'potential': Dict[str, float],
        'opportunities': Dict[str, List[Dict[str, Any]]],
        'overall_score': float
    },
    'timestamp': str
}
```

## Best Practices

1. Error Handling
   - All components include comprehensive error handling
   - Errors are logged through the MonitoringService
   - Failed operations return empty results rather than raising exceptions

2. Performance
   - Use async/await for I/O operations
   - Implement caching where appropriate
   - Monitor performance metrics

3. Configuration
   - Use configuration files for parameters
   - Validate configuration values
   - Provide sensible defaults

4. Testing
   - Write unit tests for each component
   - Test edge cases and error conditions
   - Mock external dependencies

5. Monitoring
   - Record metrics for all operations
   - Track error rates and performance
   - Monitor resource usage

## How it works

I'll explain how the strategy components integrate with the other parts of the system. Let me break down the interactions:

1. **Data Flow Overview**:
```
Scrapers (adapters/*_scraper.py) 
  → Data Models (data_models.py)
    → Pipeline (pipeline/*.py)
      → Intelligence (intelligence/*_analysis.py)
        → Strategies (strategies/*.py)
```

2. **Integration Points**:

a) **Scrapers → Data Models**:
- Scrapers collect raw data and return it as `DataObject` instances
- Example from `linkedin_scraper.py`:
```python
async def scrape_profile(self, url: str) -> DataObject:
    # Scrapes data and returns DataObject
    return DataObject(
        platform=PlatformType.LINKEDIN,
        url=url,
        data=profile_data,
        metadata={'timestamp': datetime.utcnow()}
    )
```

b) **Data Models → Pipeline**:
- Pipeline components process `DataObject` instances
- Example from `data_cleaner.py`:
```python
async def clean_data(self, data_object: DataObject) -> DataObject:
    # Cleans and validates data
    return DataObject(
        platform=data_object.platform,
        url=data_object.url,
        data=cleaned_data,
        metadata=data_object.metadata
    )
```

c) **Pipeline → Intelligence**:
- Intelligence components analyze processed data
- Example from `profile_analysis.py`:
```python
async def analyze_profile(self, data_object: DataObject) -> Dict[str, Any]:
    # Analyzes profile data
    return {
        'interests': await self._analyze_interests(data_object),
        'influence': await self._analyze_influence(data_object)
    }
```

d) **Intelligence → Strategies**:
- Strategies use intelligence analysis results for decision-making
- Example from `behavioral_patterns.py`:
```python
async def analyze_behavioral_patterns(self, user_data: Dict[str, Any], platform: str):
    # Uses intelligence analysis results
    features = await self._extract_behavioral_features(user_data, platform)
    interests = await self._analyze_interests(features)
    influence = await self._analyze_influence(features)
```

3. **Specific Strategy Integrations**:

a) **BehavioralPatternRecognition**:
- Uses data from `ProfileAnalysisAI` and `NetworkAnalysisAI`
- Processes behavioral features extracted by intelligence components
- Example:
```python
# In behavioral_patterns.py
async def _extract_behavioral_features(self, user_data: Dict[str, Any], platform: str):
    # Uses profile analysis results
    profile_analysis = user_data.get('profile_analysis', {})
    network_analysis = user_data.get('network_analysis', {})
    
    return {
        'content_activity': self._analyze_content_activity(profile_analysis),
        'interaction_patterns': self._analyze_interaction_patterns(network_analysis)
    }
```

b) **MultiDimensionalScoring**:
- Uses data from `ProspectScorer` and `CompetitiveAnalysisAI`
- Calculates scores based on intelligence analysis results
- Example:
```python
# In multi_dimensional_scoring.py
async def calculate_prospect_score(self, prospect_data: Dict[str, Any], platform: str):
    # Uses competitive analysis results
    competitive_analysis = prospect_data.get('competitive_analysis', {})
    
    dimension_scores = {
        'engagement': await self._calculate_engagement_score(prospect_data, platform),
        'influence': await self._calculate_influence_score(competitive_analysis, platform)
    }
```

c) **CompetitiveIntelligence**:
- Uses data from `CompetitiveAnalysisAI` and `TrendAnalysisAI`
- Analyzes market trends and competitor data
- Example:
```python
# In competitive_intelligence.py
async def analyze_competitive_landscape(self, market_data: Dict[str, Any], platform: str):
    # Uses trend analysis results
    trend_analysis = market_data.get('trend_analysis', {})
    
    trends = await self._analyze_market_trends(trend_analysis, platform)
    segments = await self._analyze_market_segments(market_data, platform)
```

4. **Data Flow Example**:
```python
# 1. Scraper collects data
scraper = LinkedInScraper(config)
raw_data = await scraper.scrape_profile(url)

# 2. Pipeline processes data
cleaner = DataCleaner(config)
cleaned_data = await cleaner.clean_data(raw_data)

# 3. Intelligence analyzes data
profile_analysis = ProfileAnalysisAI(config)
analysis_results = await profile_analysis.analyze_profile(cleaned_data)

# 4. Strategies make decisions
behavioral_analysis = BehavioralPatternRecognition(config)
patterns = await behavioral_analysis.analyze_behavioral_patterns(
    analysis_results,
    platform='linkedin'
)
```

5. **Error Handling and Monitoring**:
- All components use the `MonitoringService` for logging and metrics
- Errors are propagated through the system with appropriate context
- Example:
```python
# In any strategy component
try:
    result = await self._analyze_data(data)
except Exception as e:
    self.monitoring.log_error(
        f"Error in analysis: {str(e)}",
        error_type="analysis_error",
        component="strategy_component",
        context={'data': data}
    )
```

This integration ensures that:
1. Data flows smoothly through the system
2. Each component has access to the data it needs
3. Results are properly propagated
4. Errors are handled consistently
5. Performance is monitored
6. The system remains modular and maintainable

Would you like me to explain any specific integration point in more detail?


## Contributing

When adding new strategies or modifying existing ones:

1. Follow the established patterns
2. Implement comprehensive error handling
3. Add appropriate logging and metrics
4. Update documentation
5. Add unit tests
6. Consider performance implications 