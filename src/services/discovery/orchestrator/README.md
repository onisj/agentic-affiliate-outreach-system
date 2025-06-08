# Discovery Orchestrator

The Discovery Orchestrator manages and coordinates the discovery process across different platforms and components of the Agentic Affiliate Outreach System.

## Components

### Smart Scheduler
The `SmartScheduler` class manages scraping tasks across platforms:
- Intelligent task scheduling
- Rate limit management
- Resource optimization
- Task prioritization
- Concurrent task execution

### Task Manager
The `TaskManager` class coordinates task execution:
- Task lifecycle management
- Dependency handling
- Progress tracking
- Result collection
- Error handling

## Integration with System Components

### Scrapers (adapters/*_scraper.py)
```python
# Example: Scheduling a scraping task
scheduler = SmartScheduler(config)
task_id = await scheduler.schedule_task(
    task_type='profile_scrape',
    platform='linkedin',
    target='profile_url',
    priority=1
)
```

### Intelligence (intelligence/*_analysis.py)
```python
# Example: Managing analysis tasks
task_manager = TaskManager(config)
analysis_task_id = await task_manager.create_task(
    task_type='profile_analysis',
    platform='linkedin',
    target='profile_data',
    dependencies=['scraping_task_id']
)
```

### Pipeline (pipeline/*.py)
```python
# Example: Coordinating pipeline tasks
task_manager = TaskManager(config)
pipeline_task_id = await task_manager.create_task(
    task_type='data_processing',
    platform='linkedin',
    target='raw_data',
    dependencies=['scraping_task_id']
)
```

## Data Flow

1. **Task Creation**
   - Tasks are created with specific types and targets
   - Dependencies are defined
   - Timeouts are set

2. **Task Scheduling**
   - Tasks are prioritized
   - Rate limits are considered
   - Resources are allocated

3. **Task Execution**
   - Dependencies are checked
   - Progress is monitored
   - Results are collected

4. **Task Completion**
   - Results are stored
   - Dependencies are updated
   - Metrics are recorded

## Configuration

### Smart Scheduler
```python
config = {
    'max_concurrent_tasks': 5,
    'task_timeout': 300,
    'retry_attempts': 3,
    'retry_delay': 60,
    'linkedin_rate_limits': {...},
    'twitter_rate_limits': {...},
    # ... other platform rate limits
}
```

### Task Manager
```python
config = {
    'default_timeout': 300,
    'max_retries': 3,
    'retry_delay': 60,
    'result_ttl': 3600
}
```

## Usage Examples

### Scheduling Scraping Tasks
```python
# Initialize scheduler
scheduler = SmartScheduler(config)

# Schedule profile scraping
profile_task_id = await scheduler.schedule_task(
    task_type='profile_scrape',
    platform='linkedin',
    target='profile_url',
    priority=1
)

# Schedule content scraping
content_task_id = await scheduler.schedule_task(
    task_type='content_scrape',
    platform='linkedin',
    target='content_url',
    priority=2
)
```

### Managing Analysis Tasks
```python
# Initialize task manager
task_manager = TaskManager(config)

# Create analysis task
analysis_task_id = await task_manager.create_task(
    task_type='profile_analysis',
    platform='linkedin',
    target='profile_data',
    dependencies=[profile_task_id]
)

# Start task
await task_manager.start_task(analysis_task_id)

# Update progress
await task_manager.update_task_progress(analysis_task_id, 0.5)

# Complete task
await task_manager.complete_task(analysis_task_id, analysis_result)
```

### Coordinating Pipeline Tasks
```python
# Create pipeline task
pipeline_task_id = await task_manager.create_task(
    task_type='data_processing',
    platform='linkedin',
    target='raw_data',
    dependencies=[profile_task_id, content_task_id]
)

# Monitor task status
status = await task_manager.get_task_status(pipeline_task_id)

# Get task result
result = await task_manager.get_task_result(pipeline_task_id)
```

## Error Handling

### Task Failures
```python
try:
    await task_manager.start_task(task_id)
except Exception as e:
    await task_manager.fail_task(task_id, str(e))
```

### Rate Limit Handling
```python
# In SmartScheduler
rate_limiter = self.rate_limiters.get(platform)
await rate_limiter.acquire()
try:
    # Execute task
    result = await self._run_task(task)
finally:
    rate_limiter.release()
```

## Monitoring

### Task Metrics
- Created tasks
- Started tasks
- Completed tasks
- Failed tasks
- Task progress
- Task duration

### Rate Limit Metrics
- Remaining calls
- Reset times
- Rate limit hits

### Resource Metrics
- Concurrent tasks
- Queue size
- Task timeouts

## Best Practices

1. **Task Management**
   - Set appropriate timeouts
   - Define clear dependencies
   - Monitor task progress
   - Handle failures gracefully

2. **Rate Limiting**
   - Respect platform limits
   - Implement backoff strategies
   - Monitor rate limit status
   - Handle rate limit errors

3. **Resource Management**
   - Limit concurrent tasks
   - Monitor resource usage
   - Implement cleanup
   - Handle timeouts

4. **Error Handling**
   - Log all errors
   - Implement retries
   - Track error rates
   - Handle edge cases

5. **Monitoring**
   - Track task metrics
   - Monitor rate limits
   - Track resource usage
   - Set up alerts

## Contributing

When adding new features or modifying existing ones:

1. Follow the established patterns
2. Implement comprehensive error handling
3. Add appropriate logging and metrics
4. Update documentation
5. Add unit tests
6. Consider performance implications 