"""
Intelligence Service

This module implements the core intelligence service that coordinates
various intelligence components for prospect analysis and scoring.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from services.monitoring import MonitoringService

from .ai_agent import AIAgent
from .timing import TimingAnalyzer
from .personalization import PersonalizationEngine
from .sentiment import SentimentAnalyzer
from .scoring import ProspectScorer

class IntelligenceService:
    """Coordinates intelligence components for prospect analysis."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize intelligence service."""
        self.config = config or {}
        self.monitoring = MonitoringService()
        
        # Initialize components
        self.ai_agent = AIAgent(config)
        self.timing_analyzer = TimingAnalyzer(config)
        self.personalization_engine = PersonalizationEngine(config)
        self.sentiment_analyzer = SentimentAnalyzer(config)
        self.prospect_scorer = ProspectScorer(config)
        
    async def analyze_prospect(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a prospect using all intelligence components."""
        try:
            # Start timing
            start_time = datetime.utcnow()
            
            # Run analysis in parallel
            analysis_tasks = [
                self.ai_agent.analyze(prospect_data),
                self.timing_analyzer.analyze(prospect_data),
                self.personalization_engine.analyze(prospect_data),
                self.sentiment_analyzer.analyze(prospect_data)
            ]
            
            results = await asyncio.gather(*analysis_tasks)
            
            # Combine results
            analysis = {
                'ai_analysis': results[0],
                'timing_analysis': results[1],
                'personalization': results[2],
                'sentiment_analysis': results[3]
            }
            
            # Score prospect
            score = await self.prospect_scorer.score(analysis)
            
            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.monitoring.record_metric(
                'prospect_analysis_duration',
                duration,
                {'prospect_id': prospect_data.get('id')}
            )
            
            return {
                'analysis': analysis,
                'score': score,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error analyzing prospect: {str(e)}",
                error_type="analysis_error",
                component="intelligence_service",
                context={'prospect_id': prospect_data.get('id')}
            )
            raise
            
    async def get_analysis_summary(self, prospect_id: str) -> Dict[str, Any]:
        """Get summary of prospect analysis."""
        try:
            # Get analysis from components
            ai_summary = await self.ai_agent.get_summary(prospect_id)
            timing_summary = await self.timing_analyzer.get_summary(prospect_id)
            personalization_summary = await self.personalization_engine.get_summary(prospect_id)
            sentiment_summary = await self.sentiment_analyzer.get_summary(prospect_id)
            
            return {
                'ai_summary': ai_summary,
                'timing_summary': timing_summary,
                'personalization_summary': personalization_summary,
                'sentiment_summary': sentiment_summary,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error getting analysis summary: {str(e)}",
                error_type="summary_error",
                component="intelligence_service",
                context={'prospect_id': prospect_id}
            )
            raise
            
    async def cleanup(self):
        """Cleanup resources."""
        try:
            # Cleanup components
            await self.ai_agent.cleanup()
            await self.timing_analyzer.cleanup()
            await self.personalization_engine.cleanup()
            await self.sentiment_analyzer.cleanup()
            await self.prospect_scorer.cleanup()
            
        except Exception as e:
            self.monitoring.log_error(
                f"Error in cleanup: {str(e)}",
                error_type="cleanup_error",
                component="intelligence_service"
            )
            raise 