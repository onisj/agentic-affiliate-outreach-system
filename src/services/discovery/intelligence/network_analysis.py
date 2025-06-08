"""
Network Analysis AI

This module implements AI-powered network analysis for YouTube data
to support affiliate discovery.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import networkx as nx
import numpy as np
from collections import defaultdict, Counter
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from services.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class NetworkAnalysisAI:
    """AI-powered network analysis for YouTube data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        self.network = nx.Graph()
        
    async def analyze_network(self, network_data: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Analyze network from YouTube data."""
        try:
            if platform.lower() == 'youtube':
                return await self._analyze_youtube_network(network_data)
            else:
                raise ValueError(f"Unsupported platform: {platform}")
                
        except Exception as e:
            self.monitoring.log_error(
                f"Error analyzing network: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def _analyze_youtube_network(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze YouTube network."""
        try:
            # Build network graph
            self._build_network_graph(network_data)
            
            # Calculate network metrics
            network_metrics = await self._calculate_network_metrics()
            
            # Analyze community structure
            community_analysis = await self._analyze_communities()
            
            # Analyze influence flow
            influence_analysis = await self._analyze_influence_flow()
            
            # Assess collaboration potential
            collaboration_analysis = await self._assess_collaboration_potential()
            
            # Identify affiliate networks
            affiliate_networks = await self._identify_affiliate_networks()
            
            # Identify growth opportunities
            growth_opportunities = await self._identify_growth_opportunities()
            
            return {
                'network_metrics': network_metrics,
                'community_analysis': community_analysis,
                'influence_analysis': influence_analysis,
                'collaboration_analysis': collaboration_analysis,
                'affiliate_networks': affiliate_networks,
                'growth_opportunities': growth_opportunities
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing YouTube network: {str(e)}")
            raise
            
    def _build_network_graph(self, network_data: Dict[str, Any]):
        """Build network graph from data."""
        try:
            # Clear existing graph
            self.network.clear()
            
            # Add nodes (channels)
            for channel in network_data.get('channels', []):
                self.network.add_node(
                    channel['id'],
                    **channel
                )
                
            # Add edges (connections)
            for connection in network_data.get('connections', []):
                self.network.add_edge(
                    connection['source'],
                    connection['target'],
                    weight=connection.get('weight', 1.0)
                )
                
        except Exception as e:
            self.monitoring.log_error(f"Error building network graph: {str(e)}")
            raise
            
    async def _calculate_network_metrics(self) -> Dict[str, float]:
        """Calculate network metrics."""
        try:
            metrics = {
                'size': self.network.number_of_nodes(),
                'density': nx.density(self.network),
                'average_degree': sum(dict(self.network.degree()).values()) / self.network.number_of_nodes(),
                'centrality_metrics': await self._calculate_centrality_metrics(),
                'clustering_coefficient': nx.average_clustering(self.network),
                'average_path_length': nx.average_shortest_path_length(self.network) if nx.is_connected(self.network) else float('inf')
            }
            
            return metrics
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating network metrics: {str(e)}")
            return {
                'size': 0,
                'density': 0,
                'average_degree': 0,
                'centrality_metrics': {},
                'clustering_coefficient': 0,
                'average_path_length': float('inf')
            }
            
    async def _calculate_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """Calculate centrality metrics."""
        try:
            metrics = {
                'degree_centrality': nx.degree_centrality(self.network),
                'betweenness_centrality': nx.betweenness_centrality(self.network),
                'eigenvector_centrality': nx.eigenvector_centrality(self.network),
                'closeness_centrality': nx.closeness_centrality(self.network)
            }
            
            # Get top nodes for each metric
            top_nodes = {}
            for metric_name, metric_values in metrics.items():
                top_nodes[metric_name] = dict(
                    sorted(
                        metric_values.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                )
                
            return top_nodes
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating centrality metrics: {str(e)}")
            return {}
            
    async def _analyze_communities(self) -> Dict[str, Any]:
        """Analyze community structure."""
        try:
            # Detect communities using Louvain method
            communities = nx.community.louvain_communities(self.network)
            
            # Calculate community metrics
            community_metrics = {
                'number_of_communities': len(communities),
                'community_sizes': [len(c) for c in communities],
                'community_densities': [
                    nx.density(self.network.subgraph(c))
                    for c in communities
                ]
            }
            
            # Calculate inter-community connections
            inter_community_connections = defaultdict(int)
            for u, v in self.network.edges():
                for i, community in enumerate(communities):
                    if u in community:
                        for j, other_community in enumerate(communities):
                            if v in other_community and i != j:
                                inter_community_connections[(i, j)] += 1
                                
            # Calculate modularity
            modularity = nx.community.modularity(self.network, communities)
            
            return {
                'communities': [list(c) for c in communities],
                'community_metrics': community_metrics,
                'inter_community_connections': dict(inter_community_connections),
                'modularity': modularity
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing communities: {str(e)}")
            return {
                'communities': [],
                'community_metrics': {},
                'inter_community_connections': {},
                'modularity': 0
            }
            
    async def _analyze_influence_flow(self) -> Dict[str, Any]:
        """Analyze influence flow in the network."""
        try:
            # Identify key influencers
            key_influencers = self._identify_key_influencers()
            
            # Analyze influence paths
            influence_paths = self._analyze_influence_paths(key_influencers)
            
            # Calculate flow metrics
            flow_metrics = self._calculate_flow_metrics(influence_paths)
            
            return {
                'key_influencers': key_influencers,
                'influence_paths': influence_paths,
                'flow_metrics': flow_metrics
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing influence flow: {str(e)}")
            return {
                'key_influencers': [],
                'influence_paths': {},
                'flow_metrics': {}
            }
            
    def _identify_key_influencers(self) -> List[Dict[str, Any]]:
        """Identify key influencers in the network."""
        try:
            # Calculate influence scores
            influence_scores = {}
            
            # Consider multiple centrality metrics
            centrality_metrics = {
                'degree': nx.degree_centrality(self.network),
                'betweenness': nx.betweenness_centrality(self.network),
                'eigenvector': nx.eigenvector_centrality(self.network)
            }
            
            # Calculate combined influence score
            for node in self.network.nodes():
                influence_scores[node] = sum(
                    metrics[node]
                    for metrics in centrality_metrics.values()
                ) / len(centrality_metrics)
                
            # Get top influencers
            top_influencers = sorted(
                influence_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return [
                {
                    'id': node,
                    'influence_score': score,
                    'metrics': {
                        metric: centrality_metrics[metric][node]
                        for metric in centrality_metrics
                    }
                }
                for node, score in top_influencers
            ]
            
        except Exception as e:
            self.monitoring.log_error(f"Error identifying key influencers: {str(e)}")
            return []
            
    def _analyze_influence_paths(self, key_influencers: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Analyze influence paths from key influencers."""
        try:
            influence_paths = {}
            
            for influencer in key_influencers:
                influencer_id = influencer['id']
                
                # Find shortest paths to all other nodes
                paths = nx.single_source_shortest_path(
                    self.network,
                    influencer_id
                )
                
                # Filter and store paths
                influence_paths[influencer_id] = {
                    target: path
                    for target, path in paths.items()
                    if len(path) <= 3  # Consider paths of length 3 or less
                }
                
            return influence_paths
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing influence paths: {str(e)}")
            return {}
            
    def _calculate_flow_metrics(self, influence_paths: Dict[str, List[str]]) -> Dict[str, float]:
        """Calculate influence flow metrics."""
        try:
            metrics = {
                'average_path_length': 0,
                'reach_coverage': 0,
                'flow_efficiency': 0
            }
            
            if influence_paths:
                # Calculate average path length
                path_lengths = [
                    len(path)
                    for paths in influence_paths.values()
                    for path in paths.values()
                ]
                metrics['average_path_length'] = sum(path_lengths) / len(path_lengths)
                
                # Calculate reach coverage
                total_nodes = self.network.number_of_nodes()
                reached_nodes = len(set(
                    target
                    for paths in influence_paths.values()
                    for target in paths.keys()
                ))
                metrics['reach_coverage'] = reached_nodes / total_nodes
                
                # Calculate flow efficiency
                metrics['flow_efficiency'] = 1 / (metrics['average_path_length'] * (1 - metrics['reach_coverage']))
                
            return metrics
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating flow metrics: {str(e)}")
            return {
                'average_path_length': 0,
                'reach_coverage': 0,
                'flow_efficiency': 0
            }
            
    async def _assess_collaboration_potential(self) -> Dict[str, Any]:
        """Assess collaboration potential in the network."""
        try:
            # Identify potential collaborations
            potential_collaborations = self._identify_potential_collaborations()
            
            # Calculate collaboration metrics
            collaboration_metrics = self._calculate_collaboration_metrics(potential_collaborations)
            
            # Calculate synergy scores
            synergy_scores = self._calculate_synergy_scores(potential_collaborations)
            
            return {
                'potential_collaborations': potential_collaborations,
                'collaboration_metrics': collaboration_metrics,
                'synergy_scores': synergy_scores
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error assessing collaboration potential: {str(e)}")
            return {
                'potential_collaborations': [],
                'collaboration_metrics': {},
                'synergy_scores': {}
            }
            
    def _identify_potential_collaborations(self) -> List[Dict[str, Any]]:
        """Identify potential collaborations in the network."""
        try:
            potential_collaborations = []
            
            # Get node features for similarity calculation
            node_features = self._extract_node_features()
            
            # Calculate similarity matrix
            similarity_matrix = self._calculate_similarity_matrix(node_features)
            
            # Find potential collaborations
            for i, node1 in enumerate(self.network.nodes()):
                for j, node2 in enumerate(self.network.nodes()):
                    if i < j:  # Avoid duplicate pairs
                        # Check if nodes are not already connected
                        if not self.network.has_edge(node1, node2):
                            similarity = similarity_matrix[i][j]
                            if similarity > 0.5:  # Threshold for potential collaboration
                                potential_collaborations.append({
                                    'node1': node1,
                                    'node2': node2,
                                    'similarity': similarity
                                })
                                
            return sorted(
                potential_collaborations,
                key=lambda x: x['similarity'],
                reverse=True
            )
            
        except Exception as e:
            self.monitoring.log_error(f"Error identifying potential collaborations: {str(e)}")
            return []
            
    def _extract_node_features(self) -> Dict[str, List[float]]:
        """Extract features for each node."""
        try:
            features = defaultdict(list)
            
            for node in self.network.nodes():
                node_data = self.network.nodes[node]
                
                # Extract numerical features
                features['subscribers'].append(node_data.get('subscribers', 0))
                features['views'].append(node_data.get('views', 0))
                features['videos'].append(node_data.get('videos', 0))
                features['engagement_rate'].append(node_data.get('engagement_rate', 0))
                
            return features
            
        except Exception as e:
            self.monitoring.log_error(f"Error extracting node features: {str(e)}")
            return {}
            
    def _calculate_similarity_matrix(self, features: Dict[str, List[float]]) -> np.ndarray:
        """Calculate similarity matrix between nodes."""
        try:
            # Convert features to numpy array
            feature_matrix = np.array([
                features[feature]
                for feature in ['subscribers', 'views', 'videos', 'engagement_rate']
            ]).T
            
            # Normalize features
            scaler = StandardScaler()
            normalized_features = scaler.fit_transform(feature_matrix)
            
            # Calculate cosine similarity
            similarity_matrix = np.dot(normalized_features, normalized_features.T)
            
            return similarity_matrix
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating similarity matrix: {str(e)}")
            return np.array([])
            
    def _calculate_collaboration_metrics(self, potential_collaborations: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate collaboration metrics."""
        try:
            metrics = {
                'total_potential_collaborations': len(potential_collaborations),
                'average_similarity': np.mean([c['similarity'] for c in potential_collaborations]) if potential_collaborations else 0,
                'high_potential_collaborations': len([c for c in potential_collaborations if c['similarity'] > 0.7])
            }
            
            return metrics
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating collaboration metrics: {str(e)}")
            return {
                'total_potential_collaborations': 0,
                'average_similarity': 0,
                'high_potential_collaborations': 0
            }
            
    def _calculate_synergy_scores(self, potential_collaborations: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate synergy scores for potential collaborations."""
        try:
            synergy_scores = {}
            
            for collaboration in potential_collaborations:
                node1 = collaboration['node1']
                node2 = collaboration['node2']
                
                # Get node metrics
                node1_data = self.network.nodes[node1]
                node2_data = self.network.nodes[node2]
                
                # Calculate synergy score
                synergy_score = (
                    0.4 * collaboration['similarity'] +
                    0.3 * min(node1_data.get('engagement_rate', 0), node2_data.get('engagement_rate', 0)) +
                    0.3 * min(node1_data.get('subscribers', 0), node2_data.get('subscribers', 0)) / 10000
                )
                
                synergy_scores[f"{node1}-{node2}"] = synergy_score
                
            return synergy_scores
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating synergy scores: {str(e)}")
            return {}
            
    async def _identify_affiliate_networks(self) -> Dict[str, Any]:
        """Identify potential affiliate networks."""
        try:
            # Find connected components
            components = list(nx.connected_components(self.network))
            
            # Analyze each component
            affiliate_networks = []
            for component in components:
                # Create subgraph for component
                subgraph = self.network.subgraph(component)
                
                # Calculate component metrics
                metrics = {
                    'size': subgraph.number_of_nodes(),
                    'density': nx.density(subgraph),
                    'average_degree': sum(dict(subgraph.degree()).values()) / subgraph.number_of_nodes()
                }
                
                # Check for affiliate potential
                affiliate_potential = self._assess_component_affiliate_potential(subgraph)
                
                if affiliate_potential['score'] > 0.5:  # Threshold for affiliate network
                    affiliate_networks.append({
                        'nodes': list(component),
                        'metrics': metrics,
                        'affiliate_potential': affiliate_potential
                    })
                    
            return {
                'networks': affiliate_networks,
                'total_networks': len(affiliate_networks),
                'total_nodes': sum(n['metrics']['size'] for n in affiliate_networks)
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error identifying affiliate networks: {str(e)}")
            return {
                'networks': [],
                'total_networks': 0,
                'total_nodes': 0
            }
            
    def _assess_component_affiliate_potential(self, subgraph: nx.Graph) -> Dict[str, Any]:
        """Assess affiliate potential of a network component."""
        try:
            # Calculate component metrics
            metrics = {
                'average_engagement': np.mean([
                    self.network.nodes[node].get('engagement_rate', 0)
                    for node in subgraph.nodes()
                ]),
                'average_subscribers': np.mean([
                    self.network.nodes[node].get('subscribers', 0)
                    for node in subgraph.nodes()
                ]),
                'content_quality': np.mean([
                    self.network.nodes[node].get('content_quality', 0)
                    for node in subgraph.nodes()
                ])
            }
            
            # Calculate affiliate potential score
            potential_score = (
                0.4 * min(metrics['average_engagement'], 1.0) +
                0.4 * min(metrics['average_subscribers'] / 10000, 1.0) +
                0.2 * metrics['content_quality']
            )
            
            return {
                'metrics': metrics,
                'score': potential_score
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error assessing component affiliate potential: {str(e)}")
            return {
                'metrics': {},
                'score': 0
            }
            
    async def _identify_growth_opportunities(self) -> Dict[str, Any]:
        """Identify growth opportunities in the network."""
        try:
            opportunities = {
                'network_expansion': self._identify_network_expansion_opportunities(),
                'content_improvement': self._identify_content_improvement_opportunities(),
                'collaboration_opportunities': self._identify_collaboration_opportunities(),
                'audience_growth': self._identify_audience_growth_opportunities()
            }
            
            return opportunities
            
        except Exception as e:
            self.monitoring.log_error(f"Error identifying growth opportunities: {str(e)}")
            return {
                'network_expansion': [],
                'content_improvement': [],
                'collaboration_opportunities': [],
                'audience_growth': []
            }
            
    def _identify_network_expansion_opportunities(self) -> List[Dict[str, Any]]:
        """Identify network expansion opportunities."""
        try:
            opportunities = []
            
            # Find nodes with high betweenness centrality
            betweenness = nx.betweenness_centrality(self.network)
            
            for node, score in sorted(betweenness.items(), key=lambda x: x[1], reverse=True):
                if score > 0.1:  # Threshold for high betweenness
                    opportunities.append({
                        'node': node,
                        'type': 'network_expansion',
                        'score': score,
                        'recommendation': f"Focus on connecting with nodes that bridge different communities"
                    })
                    
            return opportunities
            
        except Exception as e:
            self.monitoring.log_error(f"Error identifying network expansion opportunities: {str(e)}")
            return []
            
    def _identify_content_improvement_opportunities(self) -> List[Dict[str, Any]]:
        """Identify content improvement opportunities."""
        try:
            opportunities = []
            
            for node in self.network.nodes():
                node_data = self.network.nodes[node]
                
                # Check content quality metrics
                if node_data.get('content_quality', 0) < 0.7:
                    opportunities.append({
                        'node': node,
                        'type': 'content_improvement',
                        'score': node_data.get('content_quality', 0),
                        'recommendation': "Improve content quality and consistency"
                    })
                    
            return opportunities
            
        except Exception as e:
            self.monitoring.log_error(f"Error identifying content improvement opportunities: {str(e)}")
            return []
            
    def _identify_collaboration_opportunities(self) -> List[Dict[str, Any]]:
        """Identify collaboration opportunities."""
        try:
            opportunities = []
            
            # Get potential collaborations
            potential_collaborations = self._identify_potential_collaborations()
            
            for collaboration in potential_collaborations:
                if collaboration['similarity'] > 0.7:  # High similarity threshold
                    opportunities.append({
                        'nodes': [collaboration['node1'], collaboration['node2']],
                        'type': 'collaboration',
                        'score': collaboration['similarity'],
                        'recommendation': "High potential for collaboration based on content similarity"
                    })
                    
            return opportunities
            
        except Exception as e:
            self.monitoring.log_error(f"Error identifying collaboration opportunities: {str(e)}")
            return []
            
    def _identify_audience_growth_opportunities(self) -> List[Dict[str, Any]]:
        """Identify audience growth opportunities."""
        try:
            opportunities = []
            
            for node in self.network.nodes():
                node_data = self.network.nodes[node]
                
                # Check engagement metrics
                engagement_rate = node_data.get('engagement_rate', 0)
                subscriber_growth = node_data.get('subscriber_growth_rate', 0)
                
                if engagement_rate < 0.05 or subscriber_growth < 0.1:
                    opportunities.append({
                        'node': node,
                        'type': 'audience_growth',
                        'metrics': {
                            'engagement_rate': engagement_rate,
                            'subscriber_growth': subscriber_growth
                        },
                        'recommendation': "Focus on improving engagement and subscriber growth"
                    })
                    
            return opportunities
            
        except Exception as e:
            self.monitoring.log_error(f"Error identifying audience growth opportunities: {str(e)}")
            return [] 