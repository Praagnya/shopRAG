from openai import OpenAI
from typing import List, Dict, Any
from backend.config.settings import OPENAI_API_KEY, OPENAI_MODEL


class LLMClient:
    """Client for interacting with OpenAI API."""

    def __init__(self, api_key: str = OPENAI_API_KEY, model: str = OPENAI_MODEL):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Model name to use
        """
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        self.client = OpenAI(api_key=api_key)
        self.model = model
        print(f"LLM Client initialized with model: {model}")

    def generate_response(self, query: str, product_metadata: Dict[str, Any], context_documents: List[Dict[str, Any]]) -> str:
        """Generate a response using retrieved context and product metadata.

        Args:
            query: User's question
            product_metadata: Product information (features, description, etc.)
            context_documents: List of retrieved review documents

        Returns:
            Generated response string
        """
        # Build context from product metadata and reviews
        context = self._build_context(product_metadata, context_documents)

        # Create prompt
        system_prompt = """You are a helpful retail assistant that answers questions about products based on product information and customer reviews.
Only use the information provided in the context to answer questions. If you cannot find the answer in the context, say so.
Be concise, helpful, and specific. When mentioning customer opinions, indicate if they are common or isolated cases."""

        user_prompt = f"""{context}

Question: {query}

Answer based on the product information and customer reviews above:"""

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=500
        )

        return response.choices[0].message.content

    def _build_context(self, product_metadata: Dict[str, Any], documents: List[Dict[str, Any]]) -> str:
        """Build context string from product metadata and retrieved documents.

        Args:
            product_metadata: Product information dictionary
            documents: List of review document dictionaries

        Returns:
            Formatted context string
        """
        context_parts = []

        # Add product information
        context_parts.append("=== PRODUCT INFORMATION ===\n")

        product_info = f"""Product: {product_metadata.get('title', 'Unknown Product')}
Category: {product_metadata.get('main_category', 'N/A')}
Price: ${product_metadata.get('price', 'N/A')}
Average Rating: {product_metadata.get('average_rating', 'N/A')}/5 (from {product_metadata.get('rating_number', 0)} reviews)
"""
        context_parts.append(product_info)

        # Add features if available
        features = product_metadata.get('features', [])
        if features:
            context_parts.append("\nKey Features:")
            for feature in features:
                context_parts.append(f"- {feature}")

        # Add description if available
        description = product_metadata.get('description', '')
        if description:
            context_parts.append(f"\nDescription: {description}")

        # Add customer reviews
        context_parts.append("\n\n=== CUSTOMER REVIEWS ===\n")

        for i, doc in enumerate(documents, 1):
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})

            # Format each review
            review_text = f"\nReview {i}:"
            if 'review_rating' in metadata:
                review_text += f"\nRating: {metadata['review_rating']}/5"
            if 'verified_purchase' in metadata:
                review_text += f"\nVerified Purchase: {'Yes' if metadata['verified_purchase'] else 'No'}"

            review_text += f"\n{text}\n"
            context_parts.append(review_text)

        return "\n".join(context_parts)


# Singleton instance
_llm_client_instance = None


def get_llm_client() -> LLMClient:
    """Get or create the singleton LLM client instance.

    Returns:
        LLMClient instance
    """
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance
