"""
Discovery Orchestrator

This module implements the orchestrator for the affiliate discovery process,
managing the platform adapters, intelligence processors, and data pipeline.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import asyncio
from collections import defaultdict

from services.monitoring import MonitoringService
from services.discovery.adapters.linkedin_scraper import LinkedInScraper
from services.discovery.adapters.twitter_scraper import TwitterScraper
from services.discovery.adapters.youtube_scraper import YouTubeScraper
from services.discovery.adapters.tiktok_scraper import TikTokScraper
from services.discovery.adapters.instagram_scraper import InstagramScraper
from services.discovery.adapters.reddit_scraper import RedditScraper
from services.discovery.intelligence.content_analysis import ContentAnalysisAI
from services.discovery.intelligence.profile_analysis import ProfileAnalysisAI
from services.discovery.intelligence.network_analysis import NetworkAnalysisAI
from services.discovery.intelligence.trend_analysis import TrendAnalysisAI
from services.discovery.pipeline.data_cleaner import DataCleaner
from services.discovery.pipeline.data_enricher import DataEnricher
from services.discovery.pipeline.data_validator import DataValidator
from services.discovery.pipeline.prospect_scorer import ProspectScorer

logger = logging.getLogger(__name__)

class DiscoveryOrchestrator:
    """Orchestrator for the affiliate discovery process."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        
        # Initialize platform adapters
        self.scrapers = {
            'linkedin': LinkedInScraper(config),
            'twitter': TwitterScraper(config),
            'youtube': YouTubeScraper(config),
            'tiktok': TikTokScraper(config),
            'instagram': InstagramScraper(config),
            'reddit': RedditScraper(config)
        }
        
        # Initialize intelligence processors
        self.intelligence_processors = {
            'content': ContentAnalysisAI(config),
            'profile': ProfileAnalysisAI(config),
            'network': NetworkAnalysisAI(config),
            'trend': TrendAnalysisAI(config)
        }
        
        # Initialize data pipeline components
        self.data_cleaner = DataCleaner(config)
        self.data_enricher = DataEnricher(config)
        self.data_validator = DataValidator(config)
        self.prospect_scorer = ProspectScorer(config)
        
        # Initialize task tracking
        self.active_tasks = defaultdict(list)
        self.task_results = defaultdict(dict)
        
    async def start_discovery(self, search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Start the affiliate discovery process."""
        try:
            # Initialize discovery session
            session_id = self._generate_session_id()
            self.monitoring.log_info(
                f"Starting discovery session: {session_id}",
                context={"search_criteria": search_criteria}
            )
            
            # Schedule platform-specific discovery tasks
            platform_tasks = await self._schedule_platform_tasks(search_criteria)
            
            # Wait for platform tasks to complete
            platform_results = await asyncio.gather(*platform_tasks)
            
            # Process results through intelligence pipeline
            intelligence_results = await self._process_intelligence(platform_results)
            
            # Process results through data pipeline
            pipeline_results = await self._process_pipeline(intelligence_results)
            
            # Generate final discovery report
            discovery_report = await self._generate_discovery_report(pipeline_results)
            
            self.monitoring.log_info(
                f"Completed discovery session: {session_id}",
                context={"results": discovery_report}
            )
            
            return discovery_report
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error in discovery process: {str(e)}",
                context={"search_criteria": search_criteria}
            )
            raise
            
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    async def _schedule_platform_tasks(self, search_criteria: Dict[str, Any]) -> List[asyncio.Task]:
        """Schedule discovery tasks for each platform."""
        try:
            tasks = []
            
            # Schedule tasks for each platform
            for platform, scraper in self.scrapers.items():
                if self._should_scrape_platform(platform, search_criteria):
                    task = asyncio.create_task(
                        self._run_platform_discovery(platform, scraper, search_criteria)
                    )
                    tasks.append(task)
                    self.active_tasks[platform].append(task)
            
            return tasks
            
        except Exception as e:
            self.monitoring.log_error(f"Error scheduling platform tasks: {str(e)}")
            raise
            
    def _should_scrape_platform(self, platform: str, search_criteria: Dict[str, Any]) -> bool:
        """Determine if a platform should be scraped based on search criteria."""
        try:
            # Check if platform is enabled in search criteria
            if not search_criteria.get('platforms', {}).get(platform, False):
                return False
                
            # Check platform-specific criteria
            platform_criteria = search_criteria.get('platform_criteria', {}).get(platform, {})
            
            # Check minimum requirements
            if platform_criteria.get('min_followers', 0) > 0:
                return True
            if platform_criteria.get('min_engagement', 0) > 0:
                return True
            if platform_criteria.get('keywords', []):
                return True
                
            return False
            
        except Exception as e:
            self.monitoring.log_error(f"Error checking platform criteria: {str(e)}")
            return False
            
    async def _run_platform_discovery(
        self,
        platform: str,
        scraper: Any,
        search_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run discovery process for a specific platform."""
        try:
            # Initialize scraper
            await scraper.initialize()
            
            # Discover potential affiliates
            discovered_affiliates = await scraper.discover_affiliates(search_criteria)
            
            # Extract detailed data for each affiliate
            affiliate_data = []
            for affiliate in discovered_affiliates:
                try:
                    data = await scraper.extract_affiliate_data(affiliate)
                    if data:
                        affiliate_data.append(data)
                except Exception as e:
                    self.monitoring.log_error(
                        f"Error extracting affiliate data: {str(e)}",
                        context={"platform": platform, "affiliate": affiliate}
                    )
            
            return {
                'platform': platform,
                'affiliates': affiliate_data
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error in platform discovery: {str(e)}",
                context={"platform": platform}
            )
            return {
                'platform': platform,
                'affiliates': []
            }
            
    async def _process_intelligence(self, platform_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process results through intelligence pipeline."""
        try:
            intelligence_results = {}
            
            for result in platform_results:
                platform = result['platform']
                affiliates = result['affiliates']
                
                # Process each affiliate through appropriate intelligence processor
                processed_affiliates = []
                for affiliate in affiliates:
                    try:
                        # Determine processor based on platform
                        processor = self._get_intelligence_processor(platform)
                        
                        # Process affiliate data
                        processed_data = await processor.analyze_content(
                            affiliate,
                            platform
                        )
                        
                        processed_affiliates.append(processed_data)
                        
                    except Exception as e:
                        self.monitoring.log_error(
                            f"Error processing affiliate: {str(e)}",
                            context={"platform": platform, "affiliate": affiliate}
                        )
                
                intelligence_results[platform] = processed_affiliates
            
            return intelligence_results
            
        except Exception as e:
            self.monitoring.log_error(f"Error in intelligence processing: {str(e)}")
            raise
            
    def _get_intelligence_processor(self, platform: str) -> Any:
        """Get appropriate intelligence processor for platform."""
        processor_map = {
            'linkedin': self.intelligence_processors['content'],
            'twitter': self.intelligence_processors['profile'],
            'youtube': self.intelligence_processors['network'],
            'tiktok': self.intelligence_processors['trend'],
            'instagram': self.intelligence_processors['content'],
            'reddit': self.intelligence_processors['profile']
        }
        
        return processor_map.get(platform, self.intelligence_processors['content'])
        
    async def _process_pipeline(self, intelligence_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process results through data pipeline."""
        try:
            pipeline_results = {}
            
            for platform, affiliates in intelligence_results.items():
                processed_affiliates = []
                
                for affiliate in affiliates:
                    try:
                        # Clean data
                        cleaned_data = await self.data_cleaner.clean_data(affiliate)
                        
                        # Enrich data
                        enriched_data = await self.data_enricher.enrich_data(
                            cleaned_data,
                            'profile'
                        )
                        
                        # Validate data
                        validated_data = await self.data_validator.validate_data(enriched_data)
                        
                        # Score prospect
                        scored_data = await self.prospect_scorer.score_prospect(validated_data)
                        
                        processed_affiliates.append(scored_data)
                        
                    except Exception as e:
                        self.monitoring.log_error(
                            f"Error in pipeline processing: {str(e)}",
                            context={"platform": platform, "affiliate": affiliate}
                        )
                
                pipeline_results[platform] = processed_affiliates
            
            return pipeline_results
            
        except Exception as e:
            self.monitoring.log_error(f"Error in pipeline processing: {str(e)}")
            raise
            
    async def _generate_discovery_report(self, pipeline_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final discovery report."""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'platform_results': {},
                'summary': {
                    'total_affiliates': 0,
                    'platform_breakdown': {},
                    'top_prospects': [],
                    'recommendations': []
                }
            }
            
            # Process results for each platform
            for platform, affiliates in pipeline_results.items():
                # Add platform results
                report['platform_results'][platform] = {
                    'affiliate_count': len(affiliates),
                    'top_affiliates': sorted(
                        affiliates,
                        key=lambda x: x.get('score', 0),
                        reverse=True
                    )[:5]
                }
                
                # Update summary
                report['summary']['total_affiliates'] += len(affiliates)
                report['summary']['platform_breakdown'][platform] = len(affiliates)
            
            # Generate top prospects across all platforms
            all_affiliates = []
            for platform_affiliates in pipeline_results.values():
                all_affiliates.extend(platform_affiliates)
            
            report['summary']['top_prospects'] = sorted(
                all_affiliates,
                key=lambda x: x.get('score', 0),
                reverse=True
            )[:10]
            
            # Generate recommendations
            report['summary']['recommendations'] = self._generate_recommendations(
                report['summary']['top_prospects']
            )
            
            return report
            
        except Exception as e:
            self.monitoring.log_error(f"Error generating discovery report: {str(e)}")
            raise
            
    def _generate_recommendations(self, top_prospects: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on top prospects."""
        try:
            recommendations = []
            
            # Analyze prospect patterns
            platform_distribution = Counter(p['platform'] for p in top_prospects)
            score_distribution = [p['score'] for p in top_prospects]
            
            # Generate platform-specific recommendations
            for platform, count in platform_distribution.items():
                if count >= 3:
                    recommendations.append(
                        f"Focus on {platform} as it has {count} high-scoring prospects"
                    )
            
            # Generate score-based recommendations
            avg_score = np.mean(score_distribution)
            if avg_score > 0.8:
                recommendations.append(
                    "High-quality prospects found across platforms"
                )
            elif avg_score < 0.5:
                recommendations.append(
                    "Consider refining search criteria to find higher-quality prospects"
                )
            
            # Generate engagement-based recommendations
            engagement_scores = [p.get('engagement_score', 0) for p in top_prospects]
            if np.mean(engagement_scores) > 0.7:
                recommendations.append(
                    "Prospects show strong engagement potential"
                )
            
            return recommendations
            
        except Exception as e:
            self.monitoring.log_error(f"Error generating recommendations: {str(e)}")
            return [] 