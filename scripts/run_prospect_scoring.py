import sys
import os
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from database.session import get_db
from services.prospect_scoring import ProspectScoringService
from services.visualization_service import VisualizationService
from database.models import Campaign

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize scoring service
        scoring_service = ProspectScoringService()
        
        # Train model
        logger.info("Training prospect scoring model...")
        scoring_service.train_model()
        
        # Score prospects for each campaign
        with get_db() as db:
            campaigns = db.query(Campaign).all()
            
            for campaign in campaigns:
                logger.info(f"Scoring prospects for campaign: {campaign.name}")
                top_prospects = scoring_service.get_top_prospects(campaign.id)
                
                logger.info(f"Top prospects for campaign {campaign.name}:")
                for prospect in top_prospects:
                    logger.info(f"- {prospect.name}: Score = {prospect.score:.2f}")
        
        # Export scoring metrics
        metrics_path = scoring_service.export_scoring_metrics()
        if metrics_path:
            logger.info(f"Scoring metrics exported to: {metrics_path}")
        
    except Exception as e:
        logger.error(f"Error running prospect scoring: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main() 