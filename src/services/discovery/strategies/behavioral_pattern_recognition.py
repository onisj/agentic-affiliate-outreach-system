"""
Behavioral Pattern Recognition

This module implements behavioral pattern recognition for affiliate discovery,
analyzing social media posts, engagement patterns, and network connections.
"""

import nltk
import logging
import numpy as np
import networkx as nx
from textblob import TextBlob
from collections import Counter
from nltk.corpus import stopwords
from typing import Dict, List, Any
from nltk.tokenize import word_tokenize
from services.monitoring import MonitoringService
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

class BehavioralPatternRecognition:
    """Behavioral pattern recognition for affiliate discovery."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        
        # Download required NLTK data
        try:
            nltk.download('punkt')
            nltk.download('stopwords')
        except Exception as e:
            logger.error(f"Error downloading NLTK data: {str(e)}")
            
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
    async def analyze_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze behavioral patterns from social media data."""
        try:
            # Extract data components
            posts = data.get('posts', [])
            engagement = data.get('engagement', {})
            network = data.get('network', {})
            
            # Perform NLP analysis
            nlp_analysis = await self._analyze_nlp(posts)
            
            # Analyze behavior patterns
            behavior_analysis = await self._analyze_behavior(engagement)
            
            # Analyze network connections
            network_analysis = await self._analyze_network(network)
            
            # Calculate composite score
            composite_score = await self._calculate_composite_score(
                nlp_analysis,
                behavior_analysis,
                network_analysis
            )
            
            # Rank prospects
            ranking = await self._rank_prospects(composite_score)
            
            return {
                'nlp_analysis': nlp_analysis,
                'behavior_analysis': behavior_analysis,
                'network_analysis': network_analysis,
                'composite_score': composite_score,
                'ranking': ranking
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing behavioral patterns: {str(e)}")
            raise
            
    async def _analyze_nlp(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform NLP analysis on social media posts."""
        try:
            # Extract text content
            texts = [post.get('text', '') for post in posts]
            
            # Extract interests
            interests = await self._extract_interests(texts)
            
            # Analyze sentiment
            sentiment = await self._analyze_sentiment(texts)
            
            # Analyze topics
            topics = await self._extract_topics(texts)
            
            # Analyze language patterns
            language_patterns = await self._analyze_language_patterns(texts)
            
            return {
                'interests': interests,
                'sentiment': sentiment,
                'topics': topics,
                'language_patterns': language_patterns
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error performing NLP analysis: {str(e)}")
            return {}
            
    async def _analyze_behavior(self, engagement: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze behavior patterns from engagement data."""
        try:
            # Calculate influence score
            influence_score = await self._calculate_influence_score(engagement)
            
            # Analyze engagement patterns
            engagement_patterns = await self._analyze_engagement_patterns(engagement)
            
            # Analyze interaction patterns
            interaction_patterns = await self._analyze_interaction_patterns(engagement)
            
            # Analyze response patterns
            response_patterns = await self._analyze_response_patterns(engagement)
            
            return {
                'influence_score': influence_score,
                'engagement_patterns': engagement_patterns,
                'interaction_patterns': interaction_patterns,
                'response_patterns': response_patterns
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing behavior patterns: {str(e)}")
            return {}
            
    async def _analyze_network(self, network: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network connections."""
        try:
            # Build network graph
            graph = self._build_network_graph(network)
            
            # Analyze reach
            reach_analysis = await self._analyze_reach(graph)
            
            # Analyze connections
            connection_analysis = await self._analyze_connections(graph)
            
            # Analyze community structure
            community_analysis = await self._analyze_communities(graph)
            
            return {
                'reach_analysis': reach_analysis,
                'connection_analysis': connection_analysis,
                'community_analysis': community_analysis
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing network: {str(e)}")
            return {}
            
    async def _calculate_composite_score(
        self,
        nlp_analysis: Dict[str, Any],
        behavior_analysis: Dict[str, Any],
        network_analysis: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate composite score from all analyses."""
        try:
            # Extract scores
            interest_score = nlp_analysis.get('interests', {}).get('relevance_score', 0)
            influence_score = behavior_analysis.get('influence_score', 0)
            reach_score = network_analysis.get('reach_analysis', {}).get('score', 0)
            
            # Calculate weighted composite score
            weights = {
                'interests': 0.3,
                'influence': 0.4,
                'reach': 0.3
            }
            
            composite_score = (
                interest_score * weights['interests'] +
                influence_score * weights['influence'] +
                reach_score * weights['reach']
            )
            
            return {
                'composite_score': composite_score,
                'component_scores': {
                    'interests': interest_score,
                    'influence': influence_score,
                    'reach': reach_score
                },
                'weights': weights
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating composite score: {str(e)}")
            return {}
            
    async def _rank_prospects(self, composite_score: Dict[str, float]) -> List[Dict[str, Any]]:
        """Rank prospects based on composite score."""
        try:
            # Extract scores
            scores = composite_score.get('component_scores', {})
            
            # Calculate ranking score
            ranking_score = composite_score.get('composite_score', 0)
            
            # Generate ranking
            ranking = {
                'score': ranking_score,
                'components': scores,
                'percentile': self._calculate_percentile(ranking_score),
                'recommendation': self._generate_recommendation(ranking_score)
            }
            
            return ranking
            
        except Exception as e:
            self.monitoring.log_error(f"Error ranking prospects: {str(e)}")
            return []
            
    async def _extract_interests(self, texts: List[str]) -> Dict[str, Any]:
        """Extract interests from text content."""
        try:
            # Combine texts
            combined_text = ' '.join(texts)
            
            # Tokenize and preprocess
            tokens = word_tokenize(combined_text.lower())
            tokens = [t for t in tokens if t not in self.stop_words]
            
            # Get most common interests
            interest_counts = Counter(tokens)
            top_interests = [interest for interest, _ in interest_counts.most_common(10)]
            
            # Calculate relevance score
            relevance_score = len(top_interests) / len(tokens) if tokens else 0
            
            return {
                'interests': top_interests,
                'relevance_score': relevance_score
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error extracting interests: {str(e)}")
            return {}
            
    async def _analyze_sentiment(self, texts: List[str]) -> Dict[str, float]:
        """Analyze sentiment in text content."""
        try:
            sentiments = [TextBlob(text).sentiment.polarity for text in texts]
            
            return {
                'average_sentiment': np.mean(sentiments),
                'sentiment_volatility': np.std(sentiments),
                'positive_ratio': sum(1 for s in sentiments if s > 0) / len(sentiments) if sentiments else 0
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing sentiment: {str(e)}")
            return {}
            
    async def _extract_topics(self, texts: List[str]) -> List[str]:
        """Extract topics from text content."""
        try:
            # Combine texts
            combined_text = ' '.join(texts)
            
            # Tokenize and preprocess
            tokens = word_tokenize(combined_text.lower())
            tokens = [t for t in tokens if t not in self.stop_words]
            
            # Get most common topics
            topic_counts = Counter(tokens)
            return [topic for topic, _ in topic_counts.most_common(10)]
            
        except Exception as e:
            self.monitoring.log_error(f"Error extracting topics: {str(e)}")
            return []
            
    async def _analyze_language_patterns(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze language patterns in text content."""
        try:
            # Calculate text statistics
            text_lengths = [len(text.split()) for text in texts]
            avg_length = np.mean(text_lengths) if text_lengths else 0
            
            # Analyze word frequency
            all_words = ' '.join(texts).lower().split()
            word_freq = Counter(all_words)
            
            # Analyze sentence structure
            sentences = [TextBlob(text).sentences for text in texts]
            avg_sentence_length = np.mean([len(s) for s in sentences]) if sentences else 0
            
            return {
                'avg_text_length': avg_length,
                'word_frequency': dict(word_freq.most_common(20)),
                'avg_sentence_length': avg_sentence_length
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing language patterns: {str(e)}")
            return {}
            
    async def _calculate_influence_score(self, engagement: Dict[str, Any]) -> float:
        """Calculate influence score from engagement data."""
        try:
            # Extract metrics
            followers = engagement.get('followers', 0)
            engagement_rate = engagement.get('engagement_rate', 0)
            interaction_rate = engagement.get('interaction_rate', 0)
            
            # Calculate weighted influence score
            weights = {
                'followers': 0.4,
                'engagement': 0.3,
                'interaction': 0.3
            }
            
            normalized_followers = min(followers / 10000, 1)  # Cap at 10k followers
            influence_score = (
                normalized_followers * weights['followers'] +
                engagement_rate * weights['engagement'] +
                interaction_rate * weights['interaction']
            )
            
            return influence_score
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating influence score: {str(e)}")
            return 0.0
            
    async def _analyze_engagement_patterns(self, engagement: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze engagement patterns."""
        try:
            patterns = engagement.get('patterns', {})
            
            return {
                'active_hours': patterns.get('active_hours', {}),
                'engagement_frequency': patterns.get('engagement_frequency', {}),
                'content_preferences': patterns.get('content_preferences', {})
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing engagement patterns: {str(e)}")
            return {}
            
    async def _analyze_interaction_patterns(self, engagement: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze interaction patterns."""
        try:
            interactions = engagement.get('interactions', {})
            
            return {
                'comment_patterns': interactions.get('comment_patterns', {}),
                'share_patterns': interactions.get('share_patterns', {}),
                'engagement_timing': interactions.get('engagement_timing', {})
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing interaction patterns: {str(e)}")
            return {}
            
    async def _analyze_response_patterns(self, engagement: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze response patterns."""
        try:
            responses = engagement.get('responses', {})
            
            return {
                'response_rate': responses.get('response_rate', 0),
                'response_time': responses.get('response_time', {}),
                'response_quality': responses.get('response_quality', {})
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing response patterns: {str(e)}")
            return {}
            
    def _build_network_graph(self, network: Dict[str, Any]) -> nx.Graph:
        """Build network graph from network data."""
        try:
            graph = nx.Graph()
            
            # Add nodes
            for node in network.get('nodes', []):
                graph.add_node(
                    node['id'],
                    **node.get('attributes', {})
                )
                
            # Add edges
            for edge in network.get('edges', []):
                graph.add_edge(
                    edge['source'],
                    edge['target'],
                    **edge.get('attributes', {})
                )
                
            return graph
            
        except Exception as e:
            self.monitoring.log_error(f"Error building network graph: {str(e)}")
            return nx.Graph()
            
    async def _analyze_reach(self, graph: nx.Graph) -> Dict[str, Any]:
        """Analyze reach in the network."""
        try:
            # Calculate reach metrics
            total_nodes = graph.number_of_nodes()
            total_edges = graph.number_of_edges()
            
            # Calculate average degree
            avg_degree = sum(dict(graph.degree()).values()) / total_nodes if total_nodes > 0 else 0
            
            # Calculate reach score
            reach_score = min(avg_degree / 10, 1)  # Cap at 10 connections
            
            return {
                'total_reach': total_nodes,
                'connection_density': total_edges / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0,
                'avg_degree': avg_degree,
                'score': reach_score
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing reach: {str(e)}")
            return {}
            
    async def _analyze_connections(self, graph: nx.Graph) -> Dict[str, Any]:
        """Analyze network connections."""
        try:
            # Calculate connection metrics
            degree_centrality = nx.degree_centrality(graph)
            betweenness_centrality = nx.betweenness_centrality(graph)
            
            # Calculate connection strength
            connection_strength = {
                node: graph.degree(node) / (graph.number_of_nodes() - 1)
                for node in graph.nodes()
            }
            
            return {
                'degree_centrality': degree_centrality,
                'betweenness_centrality': betweenness_centrality,
                'connection_strength': connection_strength
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing connections: {str(e)}")
            return {}
            
    async def _analyze_communities(self, graph: nx.Graph) -> Dict[str, Any]:
        """Analyze community structure in the network."""
        try:
            # Detect communities using Louvain method
            communities = nx.community.louvain_communities(graph)
            
            # Calculate community metrics
            community_sizes = [len(community) for community in communities]
            modularity = nx.community.modularity(graph, communities)
            
            return {
                'num_communities': len(communities),
                'community_sizes': community_sizes,
                'modularity': modularity
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing communities: {str(e)}")
            return {}
            
    def _calculate_percentile(self, score: float) -> float:
        """Calculate percentile rank of a score."""
        try:
            # This would typically use historical data
            # For now, return a simple normalized score
            return min(score * 100, 100)
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating percentile: {str(e)}")
            return 0.0
            
    def _generate_recommendation(self, score: float) -> str:
        """Generate recommendation based on score."""
        try:
            if score >= 0.8:
                return "High priority prospect - Strong potential for partnership"
            elif score >= 0.6:
                return "Medium priority prospect - Good potential with some development"
            elif score >= 0.4:
                return "Low priority prospect - Monitor for improvement"
            else:
                return "Not recommended at this time"
                
        except Exception as e:
            self.monitoring.log_error(f"Error generating recommendation: {str(e)}")
            return "Unable to generate recommendation" 