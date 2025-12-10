from openai import OpenAI
from typing import List, Dict, Any
import re
from backend.config.settings import OPENAI_API_KEY, OPENAI_MODEL

# LLM Monitoring Wrapper
from backend.api.llm_monitoring import monitor_llm_call


class LLMClient:
    """Client for interacting with OpenAI API."""

    def __init__(self, api_key: str = OPENAI_API_KEY, model: str = OPENAI_MODEL):
        """Initialize OpenAI client."""
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY env variable.")

        self.client = OpenAI(api_key=api_key)
        self.model = model
        print(f"LLM Client initialized with model: {model}")

    def _sanitize_text(self, text: str) -> str:
        """Remove PII (Personal Identifiable Information) from text.

        Args:
            text: Input text that may contain PII

        Returns:
            Sanitized text with PII removed
        """
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)

        # Remove phone numbers (various formats)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        text = re.sub(r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b', '[PHONE]', text)

        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[URL]', text)
        text = re.sub(r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[URL]', text)

        # Remove credit card numbers (basic pattern)
        text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', text)

        # Remove social security numbers
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)

        return text

    def _check_hallucination(self, response: str, documents: List[Dict[str, Any]]) -> None:
        """Lightweight hallucination check - logs warnings but doesn't block.

        Args:
            response: Generated response from LLM
            documents: Retrieved review documents
        """
        if not documents or not response:
            return

        # Combine all review text
        all_review_text = ' '.join([doc.get('text', '') for doc in documents]).lower()

        # Get words from response and reviews
        response_words = set(word.lower() for word in response.split() if len(word) > 3)
        review_words = set(word.lower() for word in all_review_text.split() if len(word) > 3)

        if not response_words:
            return

        # Calculate word overlap
        overlap_words = response_words & review_words
        overlap_ratio = len(overlap_words) / len(response_words)

        # Log warning if low overlap (but don't block)
        if overlap_ratio < 0.3:
            print(f"[HALLUCINATION WARNING] Low grounding detected: {overlap_ratio:.1%} word overlap")
            print(f"[HALLUCINATION WARNING] Response may contain information not directly from reviews")
        elif overlap_ratio < 0.5:
            print(f"[GROUNDING CHECK] Moderate grounding: {overlap_ratio:.1%} word overlap")
        else:
            print(f"[GROUNDING CHECK] Good grounding: {overlap_ratio:.1%} word overlap")

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

        # Create prompt with strong anti-hallucination instructions
        system_prompt = """You are a helpful retail assistant that answers questions about products based on product information and customer reviews.

CRITICAL RULES:
1. ONLY use information directly stated in the provided context
2. DO NOT make assumptions or add information not in the reviews
3. DO NOT invent product features, specifications, or customer opinions
4. If the reviews do not contain information to answer the question, clearly state: "The available reviews do not mention this aspect"
5. Summarize customer opinions briefly - avoid quoting every review
6. Keep responses short (2-3 sentences maximum)

Be brief, helpful, and direct. Stay grounded in the actual review text."""

        user_prompt = f"""{context}

Question: {query}

Answer based ONLY on the product information and customer reviews above:
"""

        # Call OpenAI API
        print(f"[LLM] Calling OpenAI API with model: {self.model}")
        print(f"[LLM] Context length: {len(context)} chars")
        print(f"[LLM] Number of reviews in context: {len(context_documents)}")

        try:
            # ------------------------------
            # USE MONITORING WRAPPER HERE
            # ------------------------------
            def _api_call():
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_completion_tokens=500
                )

            # Run through monitoring layer (records latency, errors, tokens)
            response = monitor_llm_call(
                model=self.model,
                prompt=user_prompt,
                fn=_api_call
            )

            response_text = response.choices[0].message.content
            print(f"[LLM] Response received. Length: {len(response_text) if response_text else 0} chars")

            if not response_text:
                print("[LLM] WARNING: OpenAI returned None or empty response")
                response_text = "I apologize, but I couldn't generate a response. Please try again."

            # Check hallucination grounding (teammate logic unchanged)
            self._check_hallucination(response_text, context_documents)

            return response_text

        except Exception as e:
            print(f"[LLM] ERROR calling OpenAI API: {type(e).__name__}: {e}")
            raise

    # ------------------------------------------------------------------
    # Build final context block for the model (unchanged from teammate)
    # ------------------------------------------------------------------
    def _build_context(
        self,
        product_metadata: Dict[str, Any],
        documents: List[Dict[str, Any]]
    ) -> str:

        context_parts = []

        # Basic product information
        context_parts.append("=== PRODUCT INFORMATION ===")
        context_parts.append(
            f"""
Product: {product_metadata.get('title', 'Unknown Product')}
Category: {product_metadata.get('main_category', 'N/A')}
Price: ${product_metadata.get('price', 'N/A')}
Average Rating: {product_metadata.get('average_rating', 'N/A')}/5 
({product_metadata.get('rating_number', 0)} reviews)
""")

        # Features
        features = product_metadata.get("features", [])
        if features:
            context_parts.append("\nKey Features:")
            context_parts.extend([f"- {f}" for f in features])

        # Description
        desc = product_metadata.get("description", "")
        if desc:
            context_parts.append(f"\nDescription: {desc}")

        # Add customer reviews
        context_parts.append("\n\n=== CUSTOMER REVIEWS ===\n")

        for i, doc in enumerate(documents, 1):
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})

            # Sanitize review text to remove PII
            sanitized_text = self._sanitize_text(text)

            # Format each review
            review_text = f"\nReview {i}:"
            if 'review_rating' in metadata:
                review_text += f"\nRating: {metadata['review_rating']}/5"
            if 'verified_purchase' in metadata:
                review_text += f"\nVerified Purchase: {'Yes' if metadata['verified_purchase'] else 'No'}"

            review_text += f"\n{sanitized_text}\n"
            context_parts.append(review_text)

        return "\n".join(context_parts)


# ------------------------------
# Singleton accessor
# ------------------------------
_llm_client_instance = None


def get_llm_client() -> LLMClient:
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance
