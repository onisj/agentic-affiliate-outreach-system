from typing import Dict, List
import logging
from celery import shared_task
from sqlalchemy.orm import Session
from database.session import SessionLocal
from services.intelligence.scoring import ScoringService
from services.intelligence.sentiment import SentimentAnalyzer
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name='score_prospect')
def score_prospect(prospect_id: str) -> Dict:
    """
    Score a prospect asynchronously.
    
    Args:
        prospect_id: ID of the prospect to score
        
    Returns:
        Dictionary containing scoring results
    """
    try:
        db = SessionLocal()
        scoring_service = ScoringService(db)
        
        # Score the prospect
        score = scoring_service.score_prospect(prospect_id)
        
        # Get detailed analysis
        analysis = scoring_service.analyze_prospect(prospect_id)
        
        return {
            'prospect_id': prospect_id,
            'score': score,
            'analysis': analysis
        }
    except Exception as e:
        logger.error(f"Error scoring prospect {prospect_id}: {str(e)}")
        raise
    finally:
        db.close()

@celery_app.task(name='batch_score_prospects')
def batch_score_prospects(prospect_ids: List[str]) -> List[Dict]:
    """
    Score multiple prospects asynchronously.
    
    Args:
        prospect_ids: List of prospect IDs to score
        
    Returns:
        List of dictionaries containing scoring results
    """
    try:
        db = SessionLocal()
        scoring_service = ScoringService(db)
        
        results = []
        for prospect_id in prospect_ids:
            try:
                score = scoring_service.score_prospect(prospect_id)
                results.append({
                    'prospect_id': prospect_id,
                    'score': score,
                    'status': 'success'
                })
            except Exception as e:
                logger.error(f"Error scoring prospect {prospect_id}: {str(e)}")
                results.append({
                    'prospect_id': prospect_id,
                    'error': str(e),
                    'status': 'error'
                })
        
        return results
    except Exception as e:
        logger.error(f"Error in batch scoring: {str(e)}")
        raise
    finally:
        db.close()

@celery_app.task(name='update_prospect_scores')
def update_prospect_scores() -> Dict:
    """
    Update scores for all prospects.
    
    Returns:
        Dictionary containing update results
    """
    try:
        db = SessionLocal()
        scoring_service = ScoringService(db)
        
        # Get all prospects
        prospects = db.query(AffiliateProspect).all()
        
        results = {
            'total': len(prospects),
            'updated': 0,
            'errors': 0,
            'details': []
        }
        
        for prospect in prospects:
            try:
                score = scoring_service.score_prospect(str(prospect.id))
                results['updated'] += 1
                results['details'].append({
                    'prospect_id': str(prospect.id),
                    'score': score,
                    'status': 'success'
                })
            except Exception as e:
                logger.error(f"Error updating score for prospect {prospect.id}: {str(e)}")
                results['errors'] += 1
                results['details'].append({
                    'prospect_id': str(prospect.id),
                    'error': str(e),
                    'status': 'error'
                })
        
        return results
    except Exception as e:
        logger.error(f"Error updating prospect scores: {str(e)}")
        raise
    finally:
        db.close()

@celery_app.task(name='analyze_prospect_sentiment')
def analyze_prospect_sentiment(prospect_id: str, text: str) -> Dict:
    """
    Analyze sentiment for a prospect's text.
    
    Args:
        prospect_id: ID of the prospect
        text: Text to analyze
        
    Returns:
        Dictionary containing sentiment analysis results
    """
    try:
        sentiment_analyzer = SentimentAnalyzer()
        analysis = sentiment_analyzer.analyze_sentiment(text)
        
        return {
            'prospect_id': prospect_id,
            'analysis': analysis
        }
    except Exception as e:
        logger.error(f"Error analyzing sentiment for prospect {prospect_id}: {str(e)}")
        raise

@celery_app.task(name='batch_analyze_sentiment')
def batch_analyze_sentiment(texts: List[Dict]) -> List[Dict]:
    """
    Analyze sentiment for multiple texts.
    
    Args:
        texts: List of dictionaries containing prospect_id and text
        
    Returns:
        List of dictionaries containing sentiment analysis results
    """
    try:
        sentiment_analyzer = SentimentAnalyzer()
        results = []
        
        for item in texts:
            try:
                analysis = sentiment_analyzer.analyze_sentiment(item['text'])
                results.append({
                    'prospect_id': item['prospect_id'],
                    'analysis': analysis,
                    'status': 'success'
                })
            except Exception as e:
                logger.error(f"Error analyzing sentiment for prospect {item['prospect_id']}: {str(e)}")
                results.append({
                    'prospect_id': item['prospect_id'],
                    'error': str(e),
                    'status': 'error'
                })
        
        return results
    except Exception as e:
        logger.error(f"Error in batch sentiment analysis: {str(e)}")
        raise 