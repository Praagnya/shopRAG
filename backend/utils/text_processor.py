import re
from typing import Dict, Any


def clean_text(text: str) -> str:
    """Clean and normalize text.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)

    # Remove URLs
    text = re.sub(r'http\S+|www\.\S+', '', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def combine_review_with_product(review: Dict[str, Any], product_metadata: Dict[str, Any]) -> str:
    """Combine review with product context for embedding.
    
    This creates a rich text that includes product name and review content.
    Product metadata will be added separately at query time.
    
    Args:
        review: Review dictionary with fields like title, text, rating
        product_metadata: Product metadata with title, category, etc.
        
    Returns:
        Combined text string optimized for embedding
    """
    parts = []

    # Add product name (essential context)
    product_name = product_metadata.get('title', 'Unknown Product')
    parts.append(f"Product: {product_name}")

    # Add review rating
    if 'rating' in review and review['rating']:
        parts.append(f"Rating: {review['rating']}/5 ⭐")

    # Add review title
    if 'title' in review and review['title']:
        title = clean_text(review['title'])
        if title:
            parts.append(f"Review Title: {title}")

    # Add review text
    if 'text' in review and review['text']:
        text = clean_text(review['text'])
        if text:
            parts.append(text)

    combined = "\n".join(parts)
    return combined


def should_include_review(review: Dict[str, Any]) -> bool:
    """Determine if a review should be included in the dataset.
    
    Filters out low-quality reviews.
    
    Args:
        review: Review dictionary
        
    Returns:
        True if review should be included
    """
    # Must have text
    if not review.get('text'):
        return False

    # Text must be at least 20 characters
    text = review['text'].strip()
    if len(text) < 20:
        return False

    # Must have a rating
    if not review.get('rating'):
        return False

    return True