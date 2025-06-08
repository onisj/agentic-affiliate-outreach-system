"""
Data Enricher

This module implements data enrichment for scraped data.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
import spacy
from textblob import TextBlob

from services.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class DataEnricher:
    """Enriches scraped data with additional information."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        
        # Download required NLTK data
        try:
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('vader_lexicon')
            nltk.download('averaged_perceptron_tagger')
            nltk.download('maxent_ne_chunker')
            nltk.download('words')
        except Exception as e:
            self.monitoring.log_error(f"Error downloading NLTK data: {str(e)}")
            
        # Load spaCy model
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except:
            self.nlp = spacy.blank('en')
            
    async def enrich_profile_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich profile data with additional information."""
        try:
            enriched_data = {
                'basic_info': await self._enrich_basic_info(data.get('basic_info', {})),
                'content': await self._enrich_content(data.get('content', [])),
                'engagement': await self._enrich_engagement(data.get('engagement', {})),
                'network': await self._enrich_network(data.get('network', {}))
            }
            
            return enriched_data
            
        except Exception as e:
            self.monitoring.log_error(f"Error enriching profile data: {str(e)}")
            return {}
            
    async def _enrich_basic_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich basic profile information."""
        try:
            enriched_info = info.copy()
            
            # Add sentiment analysis for bio
            if 'bio' in info:
                enriched_info['bio_sentiment'] = self._analyze_sentiment(info['bio'])
                
            # Add entity recognition for location
            if 'location' in info:
                enriched_info['location_entities'] = self._extract_entities(info['location'])
                
            # Add topic modeling for interests
            if 'interests' in info:
                enriched_info['interest_topics'] = self._extract_topics(info['interests'])
                
            # Add demographic inference
            enriched_info['demographics'] = await self._infer_demographics(info)
            
            return enriched_info
            
        except Exception as e:
            self.monitoring.log_error(f"Error enriching basic info: {str(e)}")
            return info
            
    async def _enrich_content(self, content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich content data."""
        try:
            enriched_content = []
            
            for item in content:
                enriched_item = item.copy()
                
                # Add sentiment analysis
                if 'text' in item:
                    enriched_item['sentiment'] = self._analyze_sentiment(item['text'])
                    
                # Add entity recognition
                if 'text' in item:
                    enriched_item['entities'] = self._extract_entities(item['text'])
                    
                # Add topic modeling
                if 'text' in item:
                    enriched_item['topics'] = self._extract_topics(item['text'])
                    
                # Add engagement analysis
                if 'engagement' in item:
                    enriched_item['engagement_analysis'] = self._analyze_engagement(
                        item['engagement']
                    )
                    
                enriched_content.append(enriched_item)
                
            return enriched_content
            
        except Exception as e:
            self.monitoring.log_error(f"Error enriching content: {str(e)}")
            return content
            
    async def _enrich_engagement(self, engagement: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich engagement data."""
        try:
            enriched_engagement = engagement.copy()
            
            # Add engagement trends
            enriched_engagement['trends'] = self._analyze_engagement_trends(engagement)
            
            # Add engagement patterns
            enriched_engagement['patterns'] = self._analyze_engagement_patterns(engagement)
            
            # Add engagement quality
            enriched_engagement['quality'] = self._analyze_engagement_quality(engagement)
            
            return enriched_engagement
            
        except Exception as e:
            self.monitoring.log_error(f"Error enriching engagement: {str(e)}")
            return engagement
            
    async def _enrich_network(self, network: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich network data."""
        try:
            enriched_network = network.copy()
            
            # Add network analysis
            if 'connections' in network:
                enriched_network['analysis'] = self._analyze_network(network['connections'])
                
            # Add community detection
            if 'connections' in network:
                enriched_network['communities'] = self._detect_communities(
                    network['connections']
                )
                
            # Add influence analysis
            if 'connections' in network:
                enriched_network['influence'] = self._analyze_influence(
                    network['connections']
                )
                
            return enriched_network
            
        except Exception as e:
            self.monitoring.log_error(f"Error enriching network: {str(e)}")
            return network
            
    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text."""
        try:
            # Use VADER sentiment analyzer
            sia = SentimentIntensityAnalyzer()
            sentiment = sia.polarity_scores(text)
            
            # Add TextBlob sentiment for comparison
            blob = TextBlob(text)
            sentiment['textblob'] = blob.sentiment.polarity
            
            return sentiment
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing sentiment: {str(e)}")
            return {'neg': 0, 'neu': 0, 'pos': 0, 'compound': 0, 'textblob': 0}
            
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text."""
        try:
            doc = self.nlp(text)
            entities = []
            
            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
                
            return entities
            
        except Exception as e:
            self.monitoring.log_error(f"Error extracting entities: {str(e)}")
            return []
            
    def _extract_topics(self, text: str) -> List[Dict[str, Any]]:
        """Extract topics from text."""
        try:
            # Tokenize and remove stopwords
            tokens = word_tokenize(text.lower())
            stop_words = set(stopwords.words('english'))
            tokens = [t for t in tokens if t not in stop_words]
            
            # Extract noun phrases
            doc = self.nlp(text)
            topics = []
            
            for chunk in doc.noun_chunks:
                topics.append({
                    'text': chunk.text,
                    'root': chunk.root.text,
                    'dependency': chunk.root.dep_
                })
                
            return topics
            
        except Exception as e:
            self.monitoring.log_error(f"Error extracting topics: {str(e)}")
            return []
            
    async def _infer_demographics(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Infer demographics from profile information."""
        try:
            demographics = {
                'age_group': None,
                'gender': None,
                'location': None,
                'interests': []
            }
            
            # Infer age group from content and behavior
            if 'content' in info:
                demographics['age_group'] = self._infer_age_group(info['content'])
                
            # Infer gender from name and content
            if 'name' in info:
                demographics['gender'] = self._infer_gender(info['name'])
                
            # Extract location information
            if 'location' in info:
                demographics['location'] = self._extract_location(info['location'])
                
            # Extract interests
            if 'interests' in info:
                demographics['interests'] = self._extract_interests(info['interests'])
                
            return demographics
            
        except Exception as e:
            self.monitoring.log_error(f"Error inferring demographics: {str(e)}")
            return {}
            
    def _analyze_engagement(self, engagement: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze engagement metrics."""
        try:
            analysis = {
                'trends': self._analyze_engagement_trends(engagement),
                'patterns': self._analyze_engagement_patterns(engagement),
                'quality': self._analyze_engagement_quality(engagement)
            }
            
            return analysis
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing engagement: {str(e)}")
            return {}
            
    def _analyze_engagement_trends(self, engagement: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze engagement trends."""
        try:
            trends = {
                'growth_rate': 0,
                'engagement_rate': 0,
                'viral_coefficient': 0
            }
            
            # Calculate growth rate
            if 'followers' in engagement and 'following' in engagement:
                trends['growth_rate'] = engagement['followers'] / engagement['following']
                
            # Calculate engagement rate
            if 'likes' in engagement and 'followers' in engagement:
                trends['engagement_rate'] = engagement['likes'] / engagement['followers']
                
            # Calculate viral coefficient
            if 'shares' in engagement and 'followers' in engagement:
                trends['viral_coefficient'] = engagement['shares'] / engagement['followers']
                
            return trends
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing engagement trends: {str(e)}")
            return {}
            
    def _analyze_engagement_patterns(self, engagement: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze engagement patterns."""
        try:
            patterns = {
                'temporal': {},
                'content': {},
                'audience': {}
            }
            
            # Analyze temporal patterns
            if 'timestamps' in engagement:
                patterns['temporal'] = self._analyze_temporal_patterns(
                    engagement['timestamps']
                )
                
            # Analyze content patterns
            if 'content' in engagement:
                patterns['content'] = self._analyze_content_patterns(
                    engagement['content']
                )
                
            # Analyze audience patterns
            if 'audience' in engagement:
                patterns['audience'] = self._analyze_audience_patterns(
                    engagement['audience']
                )
                
            return patterns
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing engagement patterns: {str(e)}")
            return {}
            
    def _analyze_engagement_quality(self, engagement: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze engagement quality."""
        try:
            quality = {
                'score': 0,
                'metrics': {},
                'factors': []
            }
            
            # Calculate quality score
            if all(k in engagement for k in ['likes', 'comments', 'shares']):
                quality['score'] = (
                    engagement['likes'] * 0.4 +
                    engagement['comments'] * 0.4 +
                    engagement['shares'] * 0.2
                )
                
            # Analyze quality metrics
            quality['metrics'] = {
                'interaction_depth': self._calculate_interaction_depth(engagement),
                'audience_quality': self._calculate_audience_quality(engagement),
                'content_quality': self._calculate_content_quality(engagement)
            }
            
            # Identify quality factors
            quality['factors'] = self._identify_quality_factors(engagement)
            
            return quality
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing engagement quality: {str(e)}")
            return {}
            
    def _analyze_network(self, connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze network structure."""
        try:
            analysis = {
                'metrics': self._calculate_network_metrics(connections),
                'communities': self._detect_communities(connections),
                'influence': self._analyze_influence(connections)
            }
            
            return analysis
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing network: {str(e)}")
            return {}
            
    def _calculate_network_metrics(self, connections: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate network metrics."""
        try:
            metrics = {
                'size': len(connections),
                'density': 0,
                'centrality': 0,
                'clustering': 0
            }
            
            # Calculate network density
            if metrics['size'] > 1:
                metrics['density'] = len(connections) / (metrics['size'] * (metrics['size'] - 1))
                
            # Calculate network centrality
            metrics['centrality'] = self._calculate_centrality(connections)
            
            # Calculate clustering coefficient
            metrics['clustering'] = self._calculate_clustering(connections)
            
            return metrics
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating network metrics: {str(e)}")
            return {}
            
    def _detect_communities(self, connections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect communities in the network."""
        try:
            communities = []
            
            # Implement community detection algorithm
            # This is a placeholder for actual implementation
            
            return communities
            
        except Exception as e:
            self.monitoring.log_error(f"Error detecting communities: {str(e)}")
            return []
            
    def _analyze_influence(self, connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze influence in the network."""
        try:
            influence = {
                'score': 0,
                'metrics': {},
                'factors': []
            }
            
            # Calculate influence score
            influence['score'] = self._calculate_influence_score(connections)
            
            # Analyze influence metrics
            influence['metrics'] = {
                'reach': self._calculate_reach(connections),
                'engagement': self._calculate_engagement(connections),
                'authority': self._calculate_authority(connections)
            }
            
            # Identify influence factors
            influence['factors'] = self._identify_influence_factors(connections)
            
            return influence
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing influence: {str(e)}")
            return {} 