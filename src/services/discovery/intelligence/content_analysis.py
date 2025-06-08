"""
Content Analysis AI

This module implements AI-powered content analysis for LinkedIn and Instagram data
to support affiliate discovery.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import re
from collections import Counter
import numpy as np
from textblob import TextBlob
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer

from services.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class ContentAnalysisAI:
    """AI-powered content analysis for LinkedIn and Instagram data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        
        # Download required NLTK data
        try:
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('wordnet')
        except Exception as e:
            logger.error(f"Error downloading NLTK data: {str(e)}")
            
        # Initialize NLTK components
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
    async def analyze_content(self, content: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Analyze content from LinkedIn or Instagram."""
        try:
            if platform.lower() == 'linkedin':
                return await self._analyze_linkedin_content(content)
            elif platform.lower() == 'instagram':
                return await self._analyze_instagram_content(content)
            else:
                raise ValueError(f"Unsupported platform: {platform}")
                
        except Exception as e:
            self.monitoring.log_error(
                f"Error analyzing content: {str(e)}",
                context={"platform": platform}
            )
            raise
            
    async def _analyze_linkedin_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze LinkedIn content."""
        try:
            # Extract text from LinkedIn profile
            text = self._extract_linkedin_text(content)
            
            # Perform sentiment analysis
            sentiment = await self._analyze_sentiment(text)
            
            # Extract topics
            topics = await self._extract_topics(text)
            
            # Extract keywords
            keywords = await self._extract_keywords(text)
            
            # Detect affiliate indicators
            affiliate_indicators = await self._detect_affiliate_indicators(text)
            
            # Assess content quality
            quality_metrics = await self._assess_content_quality(text)
            
            # Calculate engagement potential
            engagement_potential = await self._calculate_engagement_potential(content)
            
            return {
                'sentiment': sentiment,
                'topics': topics,
                'keywords': keywords,
                'affiliate_indicators': affiliate_indicators,
                'quality_metrics': quality_metrics,
                'engagement_potential': engagement_potential
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing LinkedIn content: {str(e)}")
            raise
            
    async def _analyze_instagram_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Instagram content."""
        try:
            # Extract text from Instagram profile and posts
            text = self._extract_instagram_text(content)
            
            # Perform sentiment analysis
            sentiment = await self._analyze_sentiment(text)
            
            # Extract topics
            topics = await self._extract_topics(text)
            
            # Extract keywords
            keywords = await self._extract_keywords(text)
            
            # Detect affiliate indicators
            affiliate_indicators = await self._detect_affiliate_indicators(text)
            
            # Assess content quality
            quality_metrics = await self._assess_content_quality(text)
            
            # Calculate engagement potential
            engagement_potential = await self._calculate_engagement_potential(content)
            
            # Analyze visual content
            visual_analysis = await self._analyze_visual_content(content)
            
            return {
                'sentiment': sentiment,
                'topics': topics,
                'keywords': keywords,
                'affiliate_indicators': affiliate_indicators,
                'quality_metrics': quality_metrics,
                'engagement_potential': engagement_potential,
                'visual_analysis': visual_analysis
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing Instagram content: {str(e)}")
            raise
            
    def _extract_linkedin_text(self, content: Dict[str, Any]) -> str:
        """Extract text from LinkedIn profile."""
        try:
            text_parts = []
            
            # Extract profile sections
            if 'headline' in content:
                text_parts.append(content['headline'])
            if 'summary' in content:
                text_parts.append(content['summary'])
            if 'experience' in content:
                for exp in content['experience']:
                    if 'description' in exp:
                        text_parts.append(exp['description'])
            if 'skills' in content:
                text_parts.extend(content['skills'])
                
            return ' '.join(text_parts)
            
        except Exception as e:
            self.monitoring.log_error(f"Error extracting LinkedIn text: {str(e)}")
            return ''
            
    def _extract_instagram_text(self, content: Dict[str, Any]) -> str:
        """Extract text from Instagram profile and posts."""
        try:
            text_parts = []
            
            # Extract profile sections
            if 'bio' in content:
                text_parts.append(content['bio'])
            if 'recent_posts' in content:
                for post in content['recent_posts']:
                    if 'caption' in post:
                        text_parts.append(post['caption'])
                    if 'comments' in post:
                        text_parts.extend(post['comments'])
                        
            return ' '.join(text_parts)
            
        except Exception as e:
            self.monitoring.log_error(f"Error extracting Instagram text: {str(e)}")
            return ''
            
    async def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze text sentiment."""
        try:
            # Calculate overall sentiment
            blob = TextBlob(text)
            sentiment = blob.sentiment
            
            # Calculate sentence-level sentiment
            sentences = blob.sentences
            sentence_sentiments = [s.sentiment.polarity for s in sentences]
            
            return {
                'polarity': sentiment.polarity,
                'subjectivity': sentiment.subjectivity,
                'sentence_sentiments': sentence_sentiments,
                'average_sentiment': np.mean(sentence_sentiments) if sentence_sentiments else 0
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing sentiment: {str(e)}")
            return {
                'polarity': 0,
                'subjectivity': 0,
                'sentence_sentiments': [],
                'average_sentiment': 0
            }
            
    async def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text."""
        try:
            # Tokenize and preprocess text
            tokens = word_tokenize(text.lower())
            tokens = [t for t in tokens if t not in self.stop_words]
            tokens = [self.lemmatizer.lemmatize(t) for t in tokens]
            
            # Calculate word frequencies
            word_freq = Counter(tokens)
            
            # Extract most common topics
            topics = [word for word, freq in word_freq.most_common(10)]
            
            return topics
            
        except Exception as e:
            self.monitoring.log_error(f"Error extracting topics: {str(e)}")
            return []
            
    async def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords using TF-IDF."""
        try:
            # Initialize TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=20,
                stop_words='english'
            )
            
            # Fit and transform text
            tfidf_matrix = vectorizer.fit_transform([text])
            
            # Get feature names
            feature_names = vectorizer.get_feature_names_out()
            
            # Get top keywords
            keywords = []
            for i in range(len(feature_names)):
                if tfidf_matrix[0, i] > 0:
                    keywords.append(feature_names[i])
                    
            return keywords
            
        except Exception as e:
            self.monitoring.log_error(f"Error extracting keywords: {str(e)}")
            return []
            
    async def _detect_affiliate_indicators(self, text: str) -> Dict[str, Any]:
        """Detect affiliate marketing indicators in text."""
        try:
            # Define affiliate marketing terms
            affiliate_terms = [
                'affiliate', 'commission', 'referral', 'partner',
                'sponsored', 'promotion', 'discount', 'code',
                'link', 'click', 'buy', 'purchase'
            ]
            
            # Count occurrences of affiliate terms
            term_counts = {}
            for term in affiliate_terms:
                count = len(re.findall(r'\b' + term + r'\b', text.lower()))
                if count > 0:
                    term_counts[term] = count
                    
            # Calculate affiliate score
            total_terms = sum(term_counts.values())
            affiliate_score = min(total_terms / 10, 1.0)  # Normalize to 0-1
            
            return {
                'term_counts': term_counts,
                'affiliate_score': affiliate_score,
                'has_affiliate_content': affiliate_score > 0.3
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error detecting affiliate indicators: {str(e)}")
            return {
                'term_counts': {},
                'affiliate_score': 0,
                'has_affiliate_content': False
            }
            
    async def _assess_content_quality(self, text: str) -> Dict[str, float]:
        """Assess content quality metrics."""
        try:
            # Calculate basic metrics
            sentences = TextBlob(text).sentences
            words = word_tokenize(text)
            
            # Calculate readability metrics
            avg_sentence_length = len(words) / len(sentences) if sentences else 0
            unique_words = len(set(words))
            vocabulary_richness = unique_words / len(words) if words else 0
            
            # Calculate content structure
            has_headings = bool(re.search(r'^#+\s', text, re.MULTILINE))
            has_lists = bool(re.search(r'^[-*]\s', text, re.MULTILINE))
            
            # Calculate overall quality score
            quality_score = (
                0.3 * (1 / (1 + np.exp(-avg_sentence_length + 10))) +  # Sentence length
                0.3 * vocabulary_richness +  # Vocabulary richness
                0.2 * (1 if has_headings else 0) +  # Structure
                0.2 * (1 if has_lists else 0)  # Formatting
            )
            
            return {
                'avg_sentence_length': avg_sentence_length,
                'vocabulary_richness': vocabulary_richness,
                'has_headings': has_headings,
                'has_lists': has_lists,
                'quality_score': quality_score
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error assessing content quality: {str(e)}")
            return {
                'avg_sentence_length': 0,
                'vocabulary_richness': 0,
                'has_headings': False,
                'has_lists': False,
                'quality_score': 0
            }
            
    async def _calculate_engagement_potential(self, content: Dict[str, Any]) -> Dict[str, float]:
        """Calculate potential engagement metrics."""
        try:
            # Extract engagement metrics
            likes = content.get('likes', 0)
            comments = content.get('comments', 0)
            shares = content.get('shares', 0)
            followers = content.get('followers', 1)  # Avoid division by zero
            
            # Calculate engagement rates
            engagement_rate = (likes + comments + shares) / followers
            comment_rate = comments / followers
            share_rate = shares / followers
            
            # Calculate interaction quality
            interaction_quality = (
                0.4 * (likes / followers) +
                0.4 * (comments / followers) +
                0.2 * (shares / followers)
            )
            
            return {
                'engagement_rate': engagement_rate,
                'comment_rate': comment_rate,
                'share_rate': share_rate,
                'interaction_quality': interaction_quality
            }
            
        except Exception as e:
            self.monitoring.log_error(f"Error calculating engagement potential: {str(e)}")
            return {
                'engagement_rate': 0,
                'comment_rate': 0,
                'share_rate': 0,
                'interaction_quality': 0
            }
            
    async def _analyze_visual_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze visual content from Instagram posts."""
        try:
            visual_metrics = {
                'post_count': len(content.get('recent_posts', [])),
                'has_videos': False,
                'has_carousel': False,
                'avg_likes': 0,
                'avg_comments': 0
            }
            
            if 'recent_posts' in content:
                posts = content['recent_posts']
                if posts:
                    # Calculate averages
                    visual_metrics['avg_likes'] = np.mean([p.get('likes', 0) for p in posts])
                    visual_metrics['avg_comments'] = np.mean([p.get('comments', 0) for p in posts])
                    
                    # Check content types
                    visual_metrics['has_videos'] = any(p.get('is_video', False) for p in posts)
                    visual_metrics['has_carousel'] = any(p.get('is_carousel', False) for p in posts)
                    
            return visual_metrics
            
        except Exception as e:
            self.monitoring.log_error(f"Error analyzing visual content: {str(e)}")
            return {
                'post_count': 0,
                'has_videos': False,
                'has_carousel': False,
                'avg_likes': 0,
                'avg_comments': 0
            } 