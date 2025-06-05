from typing import Dict, Any, List, Optional
import numpy as np
from scipy import stats
import pandas as pd
from datetime import datetime, timedelta
import logging
from sqlalchemy import func
from database.models import OutreachCampaign, MessageLog, MessageTemplate, AffiliateProspect, ABTest, ABTestResult
from database.session import get_db
import json
import os
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

class ABTestingService:
    def __init__(self):
        self.metrics = {
            'response_rate': self._calculate_response_rate,
            'positive_response_rate': self._calculate_positive_response_rate,
            'average_response_time': self._calculate_avg_response_time,
            'conversion_rate': self._calculate_conversion_rate,
            'engagement_score': self._calculate_engagement_score
        }
    
    def create_test(
        self,
        campaign_id: str,
        template_ids: List[str],
        test_duration_days: int = 7,
        sample_size_per_variant: int = 100
    ) -> Dict[str, Any]:
        """Create a new A/B test for a campaign."""
        with get_db() as db:
            campaign = db.query(OutreachCampaign).filter(OutreachCampaign.id == campaign_id).first()
            if not campaign:
                raise ValueError("Campaign not found")
            
            templates = db.query(MessageTemplate).filter(MessageTemplate.id.in_(template_ids)).all()
            if len(templates) != len(template_ids):
                raise ValueError("One or more templates not found")
            
            # Create test record
            test = ABTest(
                id=uuid.uuid4(),
                campaign_id=campaign_id,
                name=f"A/B Test {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                variants={
                    str(template.id): {
                        'name': template.name,
                        'template_id': str(template.id)
                    }
                    for template in templates
                }
            )
            
            db.add(test)
            db.commit()
            
            # Assign prospects to test groups
            self._assign_prospects_to_test(test, db, sample_size_per_variant)
            
            return {
                'id': str(test.id),
                'campaign_id': str(test.campaign_id),
                'name': test.name,
                'variants': test.variants,
                'created_at': test.created_at.isoformat()
            }
    
    def _assign_prospects_to_test(self, test: ABTest, db, sample_size_per_variant: int) -> None:
        """Assign prospects to test groups."""
        # Get eligible prospects
        prospects = db.query(AffiliateProspect).filter(
            AffiliateProspect.status == 'NEW'
        ).limit(sample_size_per_variant * len(test.variants)).all()
        
        # Randomly assign to template groups
        template_ids = list(test.variants.keys())
        for prospect in prospects:
            variant_id = np.random.choice(template_ids)
            message_log = MessageLog(
                id=uuid.uuid4(),
                prospect_id=prospect.id,
                campaign_id=test.campaign_id,
                template_id=variant_id,
                message_type='EMAIL',
                status='PENDING',
                ab_test_variant=variant_id
            )
            db.add(message_log)
        
        db.commit()
    
    def get_test_results(
        self,
        campaign_id: str,
        metric: str = 'response_rate',
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """Get A/B test results with statistical analysis."""
        if metric not in self.metrics:
            raise ValueError(f"Invalid metric: {metric}")
        
        with get_db() as db:
            # Get test configuration
            test = db.query(ABTest).filter(
                ABTest.campaign_id == campaign_id
            ).order_by(ABTest.created_at.desc()).first()
            
            if not test:
                raise ValueError("Test configuration not found")
            
            # Calculate metrics for each template
            results = {}
            for variant_id, variant_data in test.variants.items():
                metric_value = self.metrics[metric](db, campaign_id, variant_id)
                results[variant_id] = metric_value
            
            # Perform statistical analysis
            analysis = self._perform_statistical_analysis(results, confidence_level)
            
            return {
                'test_config': {
                    'id': str(test.id),
                    'name': test.name,
                    'variants': test.variants
                },
                'metric': metric,
                'results': results,
                'analysis': analysis
            }
    
    def _calculate_response_rate(self, db, campaign_id: str, variant_id: str) -> float:
        """Calculate response rate for a template."""
        total = db.query(func.count(MessageLog.id)).filter(
            MessageLog.campaign_id == campaign_id,
            MessageLog.ab_test_variant == variant_id
        ).scalar()
        
        responses = db.query(func.count(MessageLog.id)).filter(
            MessageLog.campaign_id == campaign_id,
            MessageLog.ab_test_variant == variant_id,
            MessageLog.replied_at.isnot(None)
        ).scalar()
        
        return responses / total if total > 0 else 0
    
    def _calculate_positive_response_rate(self, db, campaign_id: str, variant_id: str) -> float:
        """Calculate positive response rate for a template."""
        total = db.query(func.count(MessageLog.id)).filter(
            MessageLog.campaign_id == campaign_id,
            MessageLog.ab_test_variant == variant_id
        ).scalar()
        
        positive = db.query(func.count(MessageLog.id)).filter(
            MessageLog.campaign_id == campaign_id,
            MessageLog.ab_test_variant == variant_id,
            MessageLog.status == 'REPLIED',
            MessageLog.content.ilike('%interested%')  # Simple positive response detection
        ).scalar()
        
        return positive / total if total > 0 else 0
    
    def _calculate_avg_response_time(self, db, campaign_id: str, variant_id: str) -> float:
        """Calculate average response time for a template."""
        response_times = db.query(
            func.extract('epoch', MessageLog.replied_at - MessageLog.sent_at)
        ).filter(
            MessageLog.campaign_id == campaign_id,
            MessageLog.ab_test_variant == variant_id,
            MessageLog.replied_at.isnot(None)
        ).all()
        
        return np.mean([t[0] for t in response_times]) if response_times else 0
    
    def _calculate_conversion_rate(self, db, campaign_id: str, variant_id: str) -> float:
        """Calculate conversion rate for a template."""
        total = db.query(func.count(MessageLog.id)).filter(
            MessageLog.campaign_id == campaign_id,
            MessageLog.ab_test_variant == variant_id
        ).scalar()
        
        conversions = db.query(func.count(MessageLog.id)).filter(
            MessageLog.campaign_id == campaign_id,
            MessageLog.ab_test_variant == variant_id,
            MessageLog.status == 'REPLIED',
            MessageLog.content.ilike('%sign up%')  # Simple conversion detection
        ).scalar()
        
        return conversions / total if total > 0 else 0
    
    def _calculate_engagement_score(self, db, campaign_id: str, variant_id: str) -> float:
        """Calculate engagement score for a template."""
        # Combine multiple metrics into an engagement score
        response_rate = self._calculate_response_rate(db, campaign_id, variant_id)
        positive_rate = self._calculate_positive_response_rate(db, campaign_id, variant_id)
        conversion_rate = self._calculate_conversion_rate(db, campaign_id, variant_id)
        
        # Weighted average
        return (0.4 * response_rate + 0.4 * positive_rate + 0.2 * conversion_rate)
    
    def _perform_statistical_analysis(
        self,
        results: Dict[str, float],
        confidence_level: float
    ) -> Dict[str, Any]:
        """Perform statistical analysis on test results."""
        variant_ids = list(results.keys())
        values = list(results.values())
        
        # Calculate basic statistics
        mean = np.mean(values)
        std = np.std(values)
        
        # Perform t-test between all pairs
        comparisons = []
        for i in range(len(variant_ids)):
            for j in range(i + 1, len(variant_ids)):
                t_stat, p_value = stats.ttest_ind(
                    [values[i]],
                    [values[j]]
                )
                
                comparisons.append({
                    'variant_a': variant_ids[i],
                    'variant_b': variant_ids[j],
                    'p_value': p_value,
                    'significant': p_value < (1 - confidence_level)
                })
        
        return {
            'mean': mean,
            'std': std,
            'confidence_interval': stats.t.interval(
                confidence_level,
                len(values) - 1,
                loc=mean,
                scale=std/np.sqrt(len(values))
            ),
            'comparisons': comparisons
        }
    
    def export_test_results(
        self,
        campaign_id: str,
        output_dir: str = "reports/ab_tests"
    ) -> str:
        """Export A/B test results to a report."""
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f'ab_test_results_{campaign_id}_{timestamp}.json')
            
            # Get results for all metrics
            all_results = {}
            for metric in self.metrics.keys():
                results = self.get_test_results(campaign_id, metric)
                all_results[metric] = results
            
            # Add summary statistics
            summary = {
                'campaign_id': campaign_id,
                'timestamp': datetime.now().isoformat(),
                'metrics': {
                    metric: {
                        'winner': max(
                            results['results'].items(),
                            key=lambda x: x[1]
                        )[0]
                    }
                    for metric, results in all_results.items()
                }
            }
            
            report = {
                'summary': summary,
                'detailed_results': all_results
            }
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Test results exported to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting test results: {e}")
            return None 