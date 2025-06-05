from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from datetime import datetime
import json
import os
from pathlib import Path

from database.models import Prospect, MessageLog, Campaign
from database.session import get_db

logger = logging.getLogger(__name__)

class ProspectScoringService:
    def __init__(self, model_path: str = "models/prospect_scorer.joblib"):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self._load_or_create_model()
        
    def _load_or_create_model(self):
        """Load existing model or create a new one if it doesn't exist."""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                logger.info("Loaded existing prospect scoring model")
            else:
                self.model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
                logger.info("Created new prospect scoring model")
        except Exception as e:
            logger.error(f"Error loading/creating model: {e}")
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
    
    def _extract_features(self, prospect: Prospect) -> Dict[str, float]:
        """Extract features from a prospect for scoring."""
        with get_db() as db:
            # Get message history
            message_logs = db.query(MessageLog).filter(
                MessageLog.prospect_id == prospect.id
            ).all()
            
            # Calculate engagement metrics
            total_messages = len(message_logs)
            positive_responses = sum(1 for log in message_logs if log.response_type == "positive")
            response_rate = positive_responses / total_messages if total_messages > 0 else 0
            
            # Get social media metrics
            social_metrics = {
                "twitter_followers": prospect.twitter_followers or 0,
                "linkedin_connections": prospect.linkedin_connections or 0,
                "instagram_followers": prospect.instagram_followers or 0
            }
            
            # Calculate engagement scores
            engagement_scores = {
                "twitter_engagement": prospect.twitter_engagement_rate or 0,
                "linkedin_engagement": prospect.linkedin_engagement_rate or 0,
                "instagram_engagement": prospect.instagram_engagement_rate or 0
            }
            
            # Combine all features
            features = {
                "total_followers": sum(social_metrics.values()),
                "avg_engagement": sum(engagement_scores.values()) / len(engagement_scores) if engagement_scores else 0,
                "response_rate": response_rate,
                "message_count": total_messages,
                "positive_response_ratio": positive_responses / total_messages if total_messages > 0 else 0
            }
            
            return features
    
    def _prepare_training_data(self) -> tuple:
        """Prepare training data from historical prospect interactions."""
        with get_db() as db:
            prospects = db.query(Prospect).all()
            X = []
            y = []
            
            for prospect in prospects:
                features = self._extract_features(prospect)
                X.append(list(features.values()))
                
                # Calculate success score based on historical data
                success_score = self._calculate_success_score(prospect)
                y.append(1 if success_score > 0.7 else 0)  # Binary classification
            
            return np.array(X), np.array(y)
    
    def _calculate_success_score(self, prospect: Prospect) -> float:
        """Calculate success score based on historical interactions."""
        with get_db() as db:
            message_logs = db.query(MessageLog).filter(
                MessageLog.prospect_id == prospect.id
            ).all()
            
            if not message_logs:
                return 0.0
            
            # Calculate weighted score based on response types
            response_weights = {
                "positive": 1.0,
                "neutral": 0.5,
                "negative": 0.0
            }
            
            total_score = sum(
                response_weights.get(log.response_type, 0)
                for log in message_logs
            )
            
            return total_score / len(message_logs)
    
    def train_model(self):
        """Train the prospect scoring model."""
        try:
            X, y = self._prepare_training_data()
            
            if len(X) < 10:  # Need minimum data for training
                logger.warning("Insufficient training data")
                return
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            
            # Save model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            
            logger.info("Successfully trained and saved prospect scoring model")
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
    
    def score_prospect(self, prospect: Prospect) -> float:
        """Score a prospect using the trained model."""
        try:
            features = self._extract_features(prospect)
            X = np.array([list(features.values())])
            X_scaled = self.scaler.transform(X)
            
            # Get probability of positive class
            score = self.model.predict_proba(X_scaled)[0][1]
            
            # Update prospect score
            with get_db() as db:
                prospect.score = score
                db.commit()
            
            return score
            
        except Exception as e:
            logger.error(f"Error scoring prospect: {e}")
            return 0.0
    
    def get_top_prospects(self, campaign_id: int, limit: int = 10) -> List[Prospect]:
        """Get top prospects for a campaign based on scores."""
        with get_db() as db:
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not campaign:
                return []
            
            # Get prospects for campaign
            prospects = db.query(Prospect).filter(
                Prospect.campaign_id == campaign_id
            ).all()
            
            # Score prospects if not already scored
            for prospect in prospects:
                if prospect.score is None:
                    self.score_prospect(prospect)
            
            # Get top prospects
            top_prospects = sorted(
                prospects,
                key=lambda p: p.score if p.score is not None else 0,
                reverse=True
            )[:limit]
            
            return top_prospects
    
    def export_scoring_metrics(self, output_dir: str = "reports/scoring"):
        """Export scoring metrics and model performance."""
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f'scoring_metrics_{timestamp}.json')
            
            with get_db() as db:
                prospects = db.query(Prospect).all()
                
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'total_prospects': len(prospects),
                    'scored_prospects': sum(1 for p in prospects if p.score is not None),
                    'score_distribution': {
                        'high': sum(1 for p in prospects if p.score and p.score > 0.7),
                        'medium': sum(1 for p in prospects if p.score and 0.3 <= p.score <= 0.7),
                        'low': sum(1 for p in prospects if p.score and p.score < 0.3)
                    },
                    'model_metrics': {
                        'feature_importance': dict(zip(
                            ['total_followers', 'avg_engagement', 'response_rate', 
                             'message_count', 'positive_response_ratio'],
                            self.model.feature_importances_.tolist()
                        ))
                    }
                }
                
                with open(output_path, 'w') as f:
                    json.dump(metrics, f, indent=2)
                
                logger.info(f"Scoring metrics exported to {output_path}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error exporting scoring metrics: {e}")
            return None 