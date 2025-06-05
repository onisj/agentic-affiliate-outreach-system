from typing import Dict, Any, List
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import json
import os
from pathlib import Path

class VisualizationService:
    def __init__(self, output_dir: str = "reports/visualizations"):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    def create_score_distribution(self, scores: List[Dict[str, Any]]) -> str:
        """Create a histogram of prospect scores."""
        df = pd.DataFrame([{
            'prospect_id': result['prospect_id'],
            'score': result['score']['overall_score']
        } for result in scores])
        
        fig = px.histogram(
            df,
            x='score',
            nbins=20,
            title='Distribution of Prospect Scores',
            labels={'score': 'Score', 'count': 'Number of Prospects'},
            color_discrete_sequence=['#2E86C1']
        )
        
        fig.update_layout(
            xaxis_title="Score",
            yaxis_title="Number of Prospects",
            showlegend=False
        )
        
        output_path = os.path.join(self.output_dir, f'score_distribution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
        fig.write_html(output_path)
        return output_path
    
    def create_component_analysis(self, scores: List[Dict[str, Any]]) -> str:
        """Create a radar chart showing average scores for each component."""
        component_scores = []
        for result in scores:
            components = result['score']['component_scores']
            component_scores.append(components)
        
        df = pd.DataFrame(component_scores)
        avg_scores = df.mean()
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=avg_scores.values,
            theta=avg_scores.index,
            fill='toself',
            name='Average Scores'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            title='Average Component Scores',
            showlegend=False
        )
        
        output_path = os.path.join(self.output_dir, f'component_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
        fig.write_html(output_path)
        return output_path
    
    def create_score_trend(self, scores: List[Dict[str, Any]], time_series: List[datetime]) -> str:
        """Create a line chart showing score trends over time."""
        df = pd.DataFrame({
            'timestamp': time_series,
            'score': [result['score']['overall_score'] for result in scores]
        })
        
        fig = px.line(
            df,
            x='timestamp',
            y='score',
            title='Prospect Score Trends Over Time',
            labels={'timestamp': 'Time', 'score': 'Average Score'}
        )
        
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Average Score",
            showlegend=False
        )
        
        output_path = os.path.join(self.output_dir, f'score_trend_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
        fig.write_html(output_path)
        return output_path
    
    def create_component_correlation(self, scores: List[Dict[str, Any]]) -> str:
        """Create a heatmap showing correlations between scoring components."""
        component_scores = []
        for result in scores:
            components = result['score']['component_scores']
            component_scores.append(components)
        
        df = pd.DataFrame(component_scores)
        corr_matrix = df.corr()
        
        fig = px.imshow(
            corr_matrix,
            title='Component Score Correlations',
            color_continuous_scale='RdBu',
            aspect='auto'
        )
        
        fig.update_layout(
            xaxis_title="Component",
            yaxis_title="Component"
        )
        
        output_path = os.path.join(self.output_dir, f'component_correlation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
        fig.write_html(output_path)
        return output_path
    
    def create_top_prospects_analysis(self, scores: List[Dict[str, Any]], top_n: int = 10) -> str:
        """Create a bar chart showing the top N prospects and their component scores."""
        # Sort prospects by overall score
        sorted_scores = sorted(scores, key=lambda x: x['score']['overall_score'], reverse=True)
        top_prospects = sorted_scores[:top_n]
        
        # Prepare data for plotting
        data = []
        for prospect in top_prospects:
            components = prospect['score']['component_scores']
            for component, score in components.items():
                data.append({
                    'prospect_id': prospect['prospect_id'],
                    'component': component,
                    'score': score
                })
        
        df = pd.DataFrame(data)
        
        fig = px.bar(
            df,
            x='prospect_id',
            y='score',
            color='component',
            title=f'Top {top_n} Prospects - Component Scores',
            barmode='group'
        )
        
        fig.update_layout(
            xaxis_title="Prospect ID",
            yaxis_title="Score",
            xaxis={'tickangle': 45}
        )
        
        output_path = os.path.join(self.output_dir, f'top_prospects_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
        fig.write_html(output_path)
        return output_path
    
    def generate_all_visualizations(self, scores: List[Dict[str, Any]], time_series: List[datetime] = None) -> Dict[str, str]:
        """Generate all visualizations and return their file paths."""
        visualizations = {
            'distribution': self.create_score_distribution(scores),
            'component_analysis': self.create_component_analysis(scores),
            'component_correlation': self.create_component_correlation(scores),
            'top_prospects': self.create_top_prospects_analysis(scores)
        }
        
        if time_series:
            visualizations['trend'] = self.create_score_trend(scores, time_series)
        
        return visualizations 