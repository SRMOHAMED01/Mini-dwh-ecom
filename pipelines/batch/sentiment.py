"""
NLP Sentiment Analysis module for customer reviews using NLTK VADER.
"""
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Ensure the VADER lexicon is downloaded quietly
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

_analyzer = None


def get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


def analyze_review(title: str, content: str, product_rating: float = None) -> dict:
    """
    Analyzes sentiment of review title and content using VADER compound score.

    Returns:
        dict: {
            "score": float (-1.0 to 1.0),
            "label": "POSITIVE" | "NEUTRAL" | "NEGATIVE",
            "is_divergent": bool (rating vs. sentiment divergence)
        }
    """
    analyzer = get_analyzer()
    combined_text = f"{str(title or '').strip()}. {str(content or '').strip()}".strip()

    if not combined_text or combined_text == ".":
        return {
            "score": 0.0,
            "label": "NEUTRAL",
            "is_divergent": False,
        }

    scores = analyzer.polarity_scores(combined_text)
    compound = round(scores["compound"], 3)

    if compound >= 0.05:
        label = "POSITIVE"
    elif compound <= -0.05:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"

    # Divergence detection:
    # High star rating (>= 4.0) but negative review text (fake review or quality defect alarm)
    # Low star rating (<= 2.0) but positive review text
    is_divergent = False
    if product_rating is not None:
        try:
            rating_val = float(product_rating)
            if rating_val >= 4.0 and label == "NEGATIVE":
                is_divergent = True
            elif rating_val <= 2.0 and label == "POSITIVE":
                is_divergent = True
        except (ValueError, TypeError):
            pass

    return {
        "score": compound,
        "label": label,
        "is_divergent": is_divergent,
    }
