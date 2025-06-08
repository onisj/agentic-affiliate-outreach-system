
# Platform Adapters

## Overview

Platform Adapters is a Python package providing platform-specific adapters for scraping social media platforms and generic websites. It includes tools to extract profiles, content, and network data from LinkedIn, Twitter, YouTube, TikTok, Instagram, Reddit, and any website, with robust rate limiting and error handling.

## Features

- **Platform-Specific Scraping**: Scrape profiles, content, and network connections from LinkedIn, Twitter, YouTube, TikTok, Instagram, and Reddit.
- **Generic Web Scraping**: Extract data from any website, including basic information, content, links, and social media connections.
- **Rate Limiting**: Built-in rate limiter to prevent exceeding platform API limits, with configurable request thresholds.
- **Asynchronous Operations**: Uses `aiohttp` and `asyncio` for efficient, non-blocking HTTP requests.
- **Selenium Integration**: Leverages Selenium WebDriver for dynamic content scraping in headless Chrome.
- **Error Handling**: Comprehensive error handling with logging and monitoring via `MonitoringService`.
- **Data Standardization**: Returns data in a consistent `DataObject` format for easy integration.


## Dependencies

The package relies on the following Python libraries:

- `aiohttp`
- `beautifulsoup4`
- `selenium`
- `webdriver-manager`
- `logging`
- `asyncio`

Additionally, you need to install Chrome WebDriver for Selenium. The package uses `webdriver-manager` to handle this automatically.

## Usage

### Importing Modules

```python
from platform_adapters import (
    BaseScraper,
    LinkedInScraper,
    TwitterScraper,
    YouTubeScraper,
    TikTokScraper,
    InstagramScraper,
    RedditScraper,
    GenericWebScraper,
    RateLimiter
)
```

### Example: Scraping a LinkedIn Profile

```python
import asyncio
from platform_adapters import LinkedInScraper

async def main():
    config = {
        "timeout": 30,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
        "page_load_delay": 2
    }
    
    async with LinkedInScraper(config) as scraper:
        profile_data = await scraper.scrape_profile("https://www.linkedin.com/in/example-profile")
        print(profile_data)

asyncio.run(main())
```

### Example: Scraping Generic Website Content

```python
import asyncio
from platform_adapters import GenericWebScraper

async def main():
    config = {
        "timeout": 30,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
        "page_load_delay": 2
    }
    
    async with GenericWebScraper(config) as scraper:
        content_data = await scraper.scrape_content("https://example.com")
        print(content_data)

asyncio.run(main())
```

Refer to individual module documentation for detailed usage instructions.

## Modules

### base_scraper.py
Defines the `BaseScraper` class, providing common functionality for all platform-specific scrapers, including URL validation, HTTP headers, and resource management.

### rate_limiter.py
Implements the `RateLimiter` class to manage request limits for each platform, preventing rate limit errors.

### linkedin_scraper.py
Scrapes LinkedIn profiles, content (posts, articles), and network connections, extracting details like experience, education, and skills.

### twitter_scraper.py
Scrapes Twitter profiles, tweets, and network connections, including follower demographics and engagement metrics.

### youtube_scraper.py
Scrapes YouTube channels, videos, and network connections, extracting subscriber counts and video engagement metrics.

### tiktok_scraper.py
Scrapes TikTok profiles, videos, and network connections, including follower demographics and video engagement metrics.

### instagram_scraper.py
Scrapes Instagram profiles, posts, and network connections, extracting engagement metrics and follower demographics.

### reddit_scraper.py
Scrapes Reddit profiles, posts, comments, and network connections, including karma and subreddit activity.

### generic_scraper.py
Scrapes any website, extracting basic information, content, links, images, videos, and social media connections.

## Configuration

Each scraper requires a configuration dictionary. Example:

```python
config = {
    "timeout": 30,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
    "page_load_delay": 2
}
```

## Error Handling

All modules include robust error handling with logging via the `MonitoringService`. Rate limit errors (HTTP 429) are handled by retrying after the specified `Retry-After` period. Other errors are logged and return empty `DataObject` instances.

## Rate Limiting

The `RateLimiter` class enforces platform-specific request limits:

- **LinkedIn**: 100/min, 1000/hr, 10000/day
- **Twitter**: 300/min, 3000/hr, 30000/day
- **YouTube**: 60/min, 1000/hr, 10000/day
- **TikTok**: 60/min, 1000/hr, 10000/day
- **Instagram**: 60/min, 1000/hr, 10000/day
- **Reddit**: 60/min, 1000/hr, 10000/day
- **Generic**: 60/min, 1000/hr, 10000/day

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

