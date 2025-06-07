 from typing import Dict, List
import logging
from celery import shared_task
from sqlalchemy.orm import Session
from database.session import SessionLocal
from services.intelligence.intelligence import IntelligenceService
from services.intelligence.sentiment import SentimentAnalyzer
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name='analyze_prospect')
def analyze_prospect(prospect_id: str) -> Dict:
    """
    Analyze a prospect asynchronously.
    
    Args:
        prospect_id: ID of the prospect to analyze
        
    Returns:
        Dictionary containing analysis results
    """
    try:
        db = SessionLocal()
        intelligence_service = IntelligenceService(db)
        
        # Analyze prospect
        analysis = intelligence_service.analyze_prospect(prospect_id)
        
        return {
            'prospect_id': prospect_id,
            'analysis': analysis
        }
    except Exception as e:
        logger.error(f"Error analyzing prospect {prospect_id}: {str(e)}")
        raise
    finally:
        db.close()

@celery_app.task(name='analyze_competitor')
def analyze_competitor(competitor_id: str) -> Dict:
    """
    Analyze a competitor asynchronously.
    
    Args:
        competitor_id: ID of the competitor to analyze
        
    Returns:
        Dictionary containing analysis results
    """
    try:
        db = SessionLocal()
        intelligence_service = IntelligenceService(db)
        
        # Analyze competitor
        analysis = intelligence_service.analyze_competitor(competitor_id)
        
        return {
            'competitor_id': competitor_id,
            'analysis': analysis
        }
    except Exception as e:
        logger.error(f"Error analyzing competitor {competitor_id}: {str(e)}")
        raise
    finally:
        db.close()

@celery_app.task(name='analyze_market_trends')
def analyze_market_trends() -> Dict:
    """
    Analyze market trends asynchronously.
    
    Returns:
        Dictionary containing market analysis results
    """
    try:
        db = SessionLocal()
        intelligence_service = IntelligenceService(db)
        
        # Analyze market trends
        analysis = intelligence_service.analyze_market_trends()
        
        return {
            'analysis': analysis
        }
    except Exception as e:
        logger.error(f"Error analyzing market trends: {str(e)}")
        raise
    finally:
        db.close()

@celery_app.task(name='analyze_competitor_activity')
def analyze_competitor_activity(competitor_id: str) -> Dict:
    """
    Analyze competitor activity asynchronously.
    
    Args:
        competitor_id: ID of the competitor to analyze
        
    Returns:
        Dictionary containing activity analysis results
    """
    try:
        db = SessionLocal()
        intelligence_service = IntelligenceService(db)
        
        # Analyze competitor activity
        analysis = intelligence_service.analyze_competitor_activity(competitor_id)
        
        return {
            'competitor_id': competitor_id,
            'analysis': analysis
        }
    except Exception as e:
        logger.error(f"Error analyzing competitor activity for {competitor_id}: {str(e)}")
        raise
    finally:
        db.close()

@celery_app.task(name='analyze_prospect_engagement')
def analyze_prospect_engagement(prospect_id: str) -> Dict:
    """
    Analyze prospect engagement asynchronously.
    
    Args:
        prospect_id: ID of the prospect to analyze
        
    Returns:
        Dictionary containing engagement analysis results
    """
    try:
        db = SessionLocal()
        intelligence_service = IntelligenceService(db)
        
        # Analyze prospect engagement
        analysis = intelligence_service.analyze_prospect_engagement(prospect_id)
        
        return {
            'prospect_id': prospect_id,
            'analysis': analysis
        }
    except Exception as e:
        logger.error(f"Error analyzing prospect engagement for {prospect_id}: {str(e)}")
        raise
    finally:
        db.close()

@celery_app.task(name='batch_analyze_prospects')
def batch_analyze_prospects(prospect_ids: List[str]) -> List[Dict]:
    """
    Analyze multiple prospects asynchronously.
    
    Args:
        prospect_ids: List of prospect IDs to analyze
        
    Returns:
        List of dictionaries containing analysis results
    """
    try:
        db = SessionLocal()
        intelligence_service = IntelligenceService(db)
        
        results = []
        for prospect_id in prospect_ids:
            try:
                analysis = intelligence_service.analyze_prospect(prospect_id)
                results.append({
                    'prospect_id': prospect_id,
                    'analysis': analysis,
                    'status': 'success'
                })
            except Exception as e:
                logger.error(f"Error analyzing prospect {prospect_id}: {str(e)}")
                results.append({
                    'prospect_id': prospect_id,
                    'error': str(e),
                    'status': 'error'
                })
        
        return results
    except Exception as e:
        logger.error(f"Error in batch prospect analysis: {str(e)}")
        raise
    finally:
        db.close()

@celery_app.task(name='analyze_sentiment')
def analyze_sentiment(text: str) -> Dict:
    """
    Analyze sentiment of text asynchronously.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary containing sentiment analysis results
    """
    try:
        sentiment_analyzer = SentimentAnalyzer()
        analysis = sentiment_analyzer.analyze_sentiment(text)
        
        return {
            'analysis': analysis
        }
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise

@celery_app.task(name='batch_analyze_sentiment')
def batch_analyze_sentiment(texts: List[str]) -> List[Dict]:
    """
    Analyze sentiment of multiple texts asynchronously.
    
    Args:
        texts: List of texts to analyze
        
    Returns:
        List of dictionaries containing sentiment analysis results
    """
    try:
        sentiment_analyzer = SentimentAnalyzer()
        results = []
        
        for text in texts:
            try:
                analysis = sentiment_analyzer.analyze_sentiment(text)
                results.append({
                    'analysis': analysis,
                    'status': 'success'
                })
            except Exception as e:
                logger.error(f"Error analyzing sentiment: {str(e)}")
                results.append({
                    'error': str(e),
                    'status': 'error'
                })
        
        return results
    except Exception as e:
        logger.error(f"Error in batch sentiment analysis: {str(e)}")
        raise