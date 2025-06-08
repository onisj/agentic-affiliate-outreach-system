"""
Discovery Pipeline

This package implements the data processing pipeline for the discovery service,
handling data cleaning, validation, enrichment, and scoring of prospects.
"""

from typing import Dict, Any, List
from datetime import datetime

from .data_cleaner import DataCleaner
from .data_validator import DataValidator
from .data_enricher import DataEnricher
from .prospect_scorer import ProspectScorer

__all__ = [
    'DataCleaner',
    'DataValidator',
    'DataEnricher',
    'ProspectScorer'
]

class DiscoveryPipeline:
    """Main pipeline for processing discovery data."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize pipeline components."""
        self.config = config
        self.cleaner = DataCleaner(config)
        self.validator = DataValidator(config)
        self.enricher = DataEnricher(config)
        self.scorer = ProspectScorer(config)
        
    async def process_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a profile through the pipeline."""
        try:
            # Clean the data
            cleaned_data = self.cleaner.clean_profile_data(profile_data)
            
            # Validate the cleaned data
            validation_results = self.validator.validate_profile_data(cleaned_data)
            if not validation_results.get('is_valid', False):
                raise ValueError(f"Data validation failed: {validation_results.get('errors', [])}")
                
            # Enrich the data
            enriched_data = await self.enricher.enrich_profile_data(cleaned_data)
            
            # Score the prospect
            scoring_results = await self.scorer.score_prospect(enriched_data)
            
            return {
                'cleaned_data': cleaned_data,
                'validation_results': validation_results,
                'enriched_data': enriched_data,
                'scoring_results': scoring_results,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Pipeline processing failed: {str(e)}")
            
    async def process_batch(self, profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple profiles through the pipeline."""
        results = []
        for profile in profiles:
            try:
                result = await self.process_profile(profile)
                results.append(result)
            except Exception as e:
                # Log error but continue processing other profiles
                print(f"Error processing profile: {str(e)}")
                continue
        return results 