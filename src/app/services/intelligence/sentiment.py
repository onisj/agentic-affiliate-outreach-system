from typing import Dict, List, Optional
import logging
from textblob import TextBlob
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import re

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon')
        
        self.sia = SentimentIntensityAnalyzer()
        self.emotion_patterns = {
            'positive': [
                r'\b(great|excellent|amazing|wonderful|fantastic|perfect)\b',
                r'\b(love|like|enjoy|happy|pleased|satisfied)\b',
                r'\b(thanks|thank you|appreciate|grateful)\b'
            ],
            'negative': [
                r'\b(bad|poor|terrible|awful|horrible|worst)\b',
                r'\b(hate|dislike|angry|upset|disappointed|frustrated)\b',
                r'\b(no|never|not|don\'t|won\'t|can\'t)\b'
            ],
            'neutral': [
                r'\b(ok|okay|fine|alright|maybe|perhaps)\b',
                r'\b(think|believe|consider|maybe|possibly)\b'
            ]
        }

    async def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of text using multiple methods.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        try:
            # Clean and preprocess text
            cleaned_text = self._preprocess_text(text)
            
            # Get sentiment scores from different methods
            vader_scores = self._analyze_vader(cleaned_text)
            textblob_scores = self._analyze_textblob(cleaned_text)
            emotion_scores = self._analyze_emotions(cleaned_text)
            
            # Combine scores
            combined_score = self._combine_scores(
                vader_scores,
                textblob_scores,
                emotion_scores
            )
            
            return {
                'text': text,
                'cleaned_text': cleaned_text,
                'vader_scores': vader_scores,
                'textblob_scores': textblob_scores,
                'emotion_scores': emotion_scores,
                'combined_score': combined_score,
                'sentiment': self._get_sentiment_label(combined_score),
                'confidence': self._calculate_confidence(
                    vader_scores,
                    textblob_scores,
                    emotion_scores
                )
            }

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            raise

    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _analyze_vader(self, text: str) -> Dict:
        """Analyze sentiment using VADER."""
        try:
            scores = self.sia.polarity_scores(text)
            return {
                'compound': scores['compound'],
                'positive': scores['pos'],
                'negative': scores['neg'],
                'neutral': scores['neu']
            }
        except Exception as e:
            logger.error(f"Error in VADER analysis: {str(e)}")
            return {'compound': 0, 'positive': 0, 'negative': 0, 'neutral': 1}

    def _analyze_textblob(self, text: str) -> Dict:
        """Analyze sentiment using TextBlob."""
        try:
            blob = TextBlob(text)
            return {
                'polarity': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity
            }
        except Exception as e:
            logger.error(f"Error in TextBlob analysis: {str(e)}")
            return {'polarity': 0, 'subjectivity': 0}

    def _analyze_emotions(self, text: str) -> Dict:
        """Analyze emotional content in text."""
        try:
            emotion_counts = {
                'positive': 0,
                'negative': 0,
                'neutral': 0
            }
            
            for emotion, patterns in self.emotion_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    emotion_counts[emotion] += len(matches)
            
            total_matches = sum(emotion_counts.values())
            if total_matches > 0:
                return {
                    emotion: count / total_matches
                    for emotion, count in emotion_counts.items()
                }
            return {'positive': 0, 'negative': 0, 'neutral': 1}
            
        except Exception as e:
            logger.error(f"Error in emotion analysis: {str(e)}")
            return {'positive': 0, 'negative': 0, 'neutral': 1}

    def _combine_scores(self,
                       vader_scores: Dict,
                       textblob_scores: Dict,
                       emotion_scores: Dict) -> float:
        """Combine scores from different methods."""
        try:
            # Normalize TextBlob polarity to [-1, 1] range
            textblob_normalized = (textblob_scores['polarity'] + 1) / 2
            
            # Calculate weighted average
            combined_score = (
                vader_scores['compound'] * 0.4 +
                textblob_normalized * 0.3 +
                (emotion_scores['positive'] - emotion_scores['negative']) * 0.3
            )
            
            return combined_score
            
        except Exception as e:
            logger.error(f"Error combining scores: {str(e)}")
            return 0.0

    def _get_sentiment_label(self, score: float) -> str:
        """Convert numerical score to sentiment label."""
        if score >= 0.6:
            return 'positive'
        elif score <= 0.4:
            return 'negative'
        else:
            return 'neutral'

    def _calculate_confidence(self,
                            vader_scores: Dict,
                            textblob_scores: Dict,
                            emotion_scores: Dict) -> float:
        """Calculate confidence in sentiment analysis."""
        try:
            # Calculate agreement between methods
            vader_label = self._get_sentiment_label(vader_scores['compound'])
            textblob_label = self._get_sentiment_label(textblob_scores['polarity'])
            emotion_label = self._get_sentiment_label(
                emotion_scores['positive'] - emotion_scores['negative']
            )
            
            # Count matching labels
            labels = [vader_label, textblob_label, emotion_label]
            most_common = max(set(labels), key=labels.count)
            agreement = labels.count(most_common) / len(labels)
            
            # Calculate confidence based on agreement and score strength
            score_strength = abs(vader_scores['compound'])
            confidence = (agreement + score_strength) / 2
            
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 0.5

    async def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """
        Analyze sentiment for multiple texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of sentiment analysis results
        """
        try:
            results = []
            for text in texts:
                result = await self.analyze_sentiment(text)
                results.append(result)
            return results
            
        except Exception as e:
            logger.error(f"Error in batch analysis: {str(e)}")
            raise

    async def get_sentiment_summary(self, texts: List[str]) -> Dict:
        """
        Get summary statistics for multiple texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            Dictionary containing sentiment summary
        """
        try:
            results = await self.analyze_batch(texts)
            
            # Calculate summary statistics
            sentiment_counts = {
                'positive': 0,
                'negative': 0,
                'neutral': 0
            }
            
            total_confidence = 0
            total_score = 0
            
            for result in results:
                sentiment_counts[result['sentiment']] += 1
                total_confidence += result['confidence']
                total_score += result['combined_score']
            
            return {
                'total_texts': len(texts),
                'sentiment_distribution': {
                    sentiment: count / len(texts)
                    for sentiment, count in sentiment_counts.items()
                },
                'average_confidence': total_confidence / len(texts),
                'average_score': total_score / len(texts),
                'dominant_sentiment': max(
                    sentiment_counts.items(),
                    key=lambda x: x[1]
                )[0]
            }
            
        except Exception as e:
            logger.error(f"Error generating sentiment summary: {str(e)}")
            raise 