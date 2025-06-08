"""
Reddit Scraper

This module implements scraping functionality for Reddit profiles and content.
"""

from typing import Dict, List, Any
import logging
import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from aiohttp import ClientResponseError

from discovery.models.data_object import DataObject
from .base_scraper import BaseScraper
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class RedditScraper(BaseScraper):
    """Scrapes data from Reddit profiles and content."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rate_limiter = RateLimiter(config)
        
    async def scrape_profile(self, profile_url: str) -> DataObject:
        """Scrape a Reddit profile."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('reddit')
            
            if not self._validate_url(profile_url):
                raise ValueError(f"Invalid profile URL: {profile_url}")
                
            profile_url = self._normalize_url(profile_url)
            self.driver.get(profile_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='user-profile']"))
            )
            
            profile_data = {
                'basic_info': await self._extract_basic_info(),
                'posts': await self._extract_posts(),
                'comments': await self._extract_comments(),
                'karma': await self._extract_karma(),
                'engagement': await self._extract_engagement()
            }
            
            logger.info(f"Successfully scraped Reddit profile: {profile_url}")
            return self._to_data_object("Reddit", profile_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_profile(profile_url)
            self._handle_error(e, f"scraping Reddit profile {profile_url}")
            return self._to_data_object("Reddit", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping Reddit profile {profile_url}")
            return self._to_data_object("Reddit", {})
            
    async def scrape_content(self, content_url: str) -> DataObject:
        """Scrape specific Reddit content."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('reddit')
            
            if not self._validate_url(content_url):
                raise ValueError(f"Invalid content URL: {content_url}")
                
            content_url = self._normalize_url(content_url)
            self.driver.get(content_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='post-container']"))
            )
            
            content_data = await self._extract_post_details()
            logger.info(f"Successfully scraped Reddit content: {content_url}")
            return self._to_data_object("Reddit", content_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_content(content_url)
            self._handle_error(e, f"scraping Reddit content {content_url}")
            return self._to_data_object("Reddit", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping Reddit content {content_url}")
            return self._to_data_object("Reddit", {})
            
    async def scrape_network(self, profile_url: str) -> DataObject:
        """Scrape network connections from a Reddit profile."""
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire('reddit')
            
            if not self._validate_url(profile_url):
                raise ValueError(f"Invalid profile URL: {profile_url}")
                
            profile_url = self._normalize_url(profile_url)
            self.driver.get(profile_url)
            await asyncio.sleep(self.config.get('page_load_delay', 2))
            
            WebDriverWait(self.driver, self.config.get('timeout', 10)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='user-profile']"))
            )
            
            network_data = {
                'subreddits': await self._extract_subreddits(),
                'moderated_communities': await self._extract_moderated_communities(),
                'trophies': await self._extract_trophies()
            }
            logger.info(f"Successfully scraped Reddit network: {profile_url}")
            return self._to_data_object("Reddit", network_data)
            
        except ClientResponseError as e:
            if e.status == 429:
                retry_after = int(e.headers.get('Retry-After', 60))
                await self._handle_rate_limit(retry_after)
                return await self.scrape_network(profile_url)
            self._handle_error(e, f"scraping Reddit network {profile_url}")
            return self._to_data_object("Reddit", {})
            
        except Exception as e:
            self._handle_error(e, f"scraping Reddit network {profile_url}")
            return self._to_data_object("Reddit", {})
            
    async def _extract_basic_info(self) -> Dict[str, Any]:
        """Extract basic profile information."""
        try:
            profile = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='user-profile']")
            basic_info = {
                'username': self._get_element_text(profile, "[data-testid='user-profile-username']"),
                'cake_day': self._get_element_text(profile, "[data-testid='user-profile-cakeday']"),
                'profile_picture': self._get_element_attribute(profile, "[data-testid='user-profile-avatar'] img", "src"),
                'verified': bool(profile.find_elements(By.CSS_SELECTOR, "[data-testid='user-profile-verified']")),
                'metadata': self._extract_metadata(profile)
            }
            return basic_info
            
        except Exception as e:
            self._handle_error(e, "extracting Reddit basic info")
            return {}
            
    async def _extract_posts(self) -> List[Dict[str, Any]]:
        """Extract posts from the profile."""
        try:
            posts = []
            post_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='post-container']")
            
            for element in post_elements:
                post = {
                    'title': self._get_element_text(element, "[data-testid='post-title']"),
                    'url': self._get_element_attribute(element, "a", "href"),
                    'subreddit': self._get_element_text(element, "[data-testid='subreddit-name']"),
                    'score': self._parse_count(self._get_element_text(element, "[data-testid='post-score']")),
                    'comments': self._parse_count(self._get_element_text(element, "[data-testid='post-comments']")),
                    'timestamp': self._get_element_attribute(element, "time", "datetime"),
                    'metadata': self._extract_metadata(element)
                }
                posts.append(post)
                
            return posts
            
        except Exception as e:
            self._handle_error(e, "extracting Reddit posts")
            return []
            
    async def _extract_comments(self) -> List[Dict[str, Any]]:
        """Extract comments from the profile."""
        try:
            comments = []
            comment_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='comment']")
            
            for element in comment_elements:
                comment = {
                    'text': self._get_element_text(element, "[data-testid='comment-text']"),
                    'subreddit': self._get_element_text(element, "[data-testid='subreddit-name']"),
                    'score': self._parse_count(self._get_element_text(element, "[data-testid='comment-score']")),
                    'timestamp': self._get_element_attribute(element, "time", "datetime"),
                    'metadata': self._extract_metadata(element)
                }
                comments.append(comment)
                
            return comments
            
        except Exception as e:
            self._handle_error(e, "extracting Reddit comments")
            return []
            
    async def _extract_karma(self) -> Dict[str, int]:
        """Extract karma information."""
        try:
            karma_section = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='user-profile-karma']")
            karma = {
                'post_karma': self._parse_count(self._get_element_text(karma_section, "[data-testid='post-karma']")),
                'comment_karma': self._parse_count(self._get_element_text(karma_section, "[data-testid='comment-karma']")),
                'total_karma': self._parse_count(self._get_element_text(karma_section, "[data-testid='total-karma']")),
                'metadata': self._extract_metadata(karma_section)
            }
            return karma
            
        except Exception as e:
            self._handle_error(e, "extracting Reddit karma")
            return {}
            
    async def _extract_engagement(self) -> Dict[str, Any]:
        """Extract engagement metrics."""
        try:
            engagement = {
                'posts': await self._get_post_engagement_metrics(),
                'comments': await self._get_comment_engagement_metrics(),
                'profile': await self._get_profile_engagement_metrics()
            }
            return engagement
            
        except Exception as e:
            self._handle_error(e, "extracting Reddit engagement")
            return {}
            
    async def _extract_post_details(self) -> Dict[str, Any]:
        """Extract detailed post information."""
        try:
            post = {
                'title': self._get_element_text(self.driver, "[data-testid='post-title']"),
                'text': self._get_element_text(self.driver, "[data-testid='post-text']"),
                'subreddit': self._get_element_text(self.driver, "[data-testid='subreddit-name']"),
                'author': self._get_element_text(self.driver, "[data-testid='post-author']"),
                'score': self._parse_count(self._get_element_text(self.driver, "[data-testid='post-score']")),
                'comments': self._parse_count(self._get_element_text(self.driver, "[data-testid='post-comments']")),
                'timestamp': self._get_element_attribute(self.driver, "time", "datetime"),
                'metadata': self._extract_metadata(self.driver)
            }
            return post
            
        except Exception as e:
            self._handle_error(e, "extracting Reddit post details")
            return {}
            
    async def _extract_subreddits(self) -> List[Dict[str, Any]]:
        """Extract subreddits the user is active in."""
        try:
            subreddits = []
            subreddit_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='subreddit-item']")
            
            for element in subreddit_elements:
                subreddit = {
                    'name': self._get_element_text(element, "[data-testid='subreddit-name']"),
                    'url': self._get_element_attribute(element, "a", "href"),
                    'subscribers': self._parse_count(self._get_element_text(element, "[data-testid='subreddit-subscribers']")),
                    'metadata': self._extract_metadata(element)
                }
                subreddits.append(subreddit)
                
            return subreddits
            
        except Exception as e:
            self._handle_error(e, "extracting Reddit subreddits")
            return []
            
    async def _extract_moderated_communities(self) -> List[Dict[str, Any]]:
        """Extract communities the user moderates."""
        try:
            communities = []
            community_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='moderated-community']")
            
            for element in community_elements:
                community = {
                    'name': self._get_element_text(element, "[data-testid='community-name']"),
                    'url': self._get_element_attribute(element, "a", "href"),
                    'subscribers': self._parse_count(self._get_element_text(element, "[data-testid='community-subscribers']")),
                    'metadata': self._extract_metadata(element)
                }
                communities.append(community)
                
            return communities
            
        except Exception as e:
            self._handle_error(e, "extracting Reddit moderated communities")
            return []
            
    async def _extract_trophies(self) -> List[Dict[str, Any]]:
        """Extract user trophies."""
        try:
            trophies = []
            trophy_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='trophy-item']")
            
            for element in trophy_elements:
                trophy = {
                    'name': self._get_element_text(element, "[data-testid='trophy-name']"),
                    'description': self._get_element_text(element, "[data-testid='trophy-description']"),
                    'icon': self._get_element_attribute(element, "img", "src"),
                    'metadata': self._extract_metadata(element)
                }
                trophies.append(trophy)
                
            return trophies
            
        except Exception as e:
            self._handle_error(e, "extracting Reddit trophies")
            return []
            
    async def _get_post_engagement_metrics(self) -> Dict[str, float]:
        """Get post engagement metrics."""
        try:
            metrics = {
                'average_score': 0,
                'average_comments': 0,
                'engagement_rate': 0
            }
            
            posts = await self._extract_posts()
            if posts:
                total_score = sum(post['score'] for post in posts)
                total_comments = sum(post['comments'] for post in posts)
                
                metrics['average_score'] = total_score / len(posts)
                metrics['average_comments'] = total_comments / len(posts)
                
                total_engagement = total_score + total_comments
                metrics['engagement_rate'] = total_engagement / len(posts)
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting Reddit post engagement metrics")
            return {}
            
    async def _get_comment_engagement_metrics(self) -> Dict[str, float]:
        """Get comment engagement metrics."""
        try:
            metrics = {
                'average_score': 0,
                'engagement_rate': 0
            }
            
            comments = await self._extract_comments()
            if comments:
                total_score = sum(comment['score'] for comment in comments)
                
                metrics['average_score'] = total_score / len(comments)
                metrics['engagement_rate'] = total_score / len(comments)
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting Reddit comment engagement metrics")
            return {}
            
    async def _get_profile_engagement_metrics(self) -> Dict[str, float]:
        """Get profile engagement metrics."""
        try:
            metrics = {
                'profile_views': 0,
                'profile_engagement_rate': 0,
                'karma_growth_rate': 0
            }
            
            profile = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='user-profile']")
            views_element = profile.find_element(By.CSS_SELECTOR, "[data-testid='user-profile-views']")
            if views_element:
                metrics['profile_views'] = self._parse_count(views_element.text)
                
            return metrics
            
        except Exception as e:
            self._handle_error(e, "getting Reddit profile engagement metrics")
            return {} 