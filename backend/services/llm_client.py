from openai import OpenAI
from typing import List, Dict, Any
from backend.config.settings import OPENAI_API_KEY, OPENAI_MODEL

# LLM Monitoring Wrapper
from backend.api.llm_monitoring import monitor_llm_call, record_llm_metrics


class LLMClient:
    """Client for interacting with OpenAI API."""

    def __init__(self, api_key: str = OPENAI_API_KEY, model: str = OPENAI_MODEL):
        """Initialize OpenAI client."""
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY env variable.")

        self.client = OpenAI(api_key=api_key)
        self.model = model
        print(f"LLM Client initialized with model: {model}")

    def generate_response(
        self,
        query: str,
        product_metadata: Dict[str, Any],
        context_documents: List[Dict[str, Any]]
    ) -> str:
        """
        Generates LLM response while also logging usage, latency, and tokens.
        """

        # Build context
        context = self._build_context(product_metadata, context_documents)

        # System instruction
        system_prompt = (
            "You are a helpful retail assistant that answers questions about products based on "
            "product information and customer reviews. Only use the provided context. "
            "If the answer is not in the context, say so."
        )

        # Final formatted prompt
        user_prompt = f"""{context}

Question: {query}

Answer based ONLY on the product information and customer reviews above:
"""

        # -------------------------
        # ✔ MONITORING WRAPPER CALL
        # -------------------------
        def _api_call():
            """Inner function passed into monitor_llm_call (actual OpenAI call)."""
            return self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=500,
            )

        # monitor_llm_call now returns:
        # (response, metrics_dict)
        response, info = monitor_llm_call(
            model=self.model,
            prompt=user_prompt,
            fn=_api_call
        )

        # Extract usage metrics safely
        prompt_tokens = info.get("prompt_tokens", 0)
        completion_tokens = info.get("completion_tokens", 0)
        latency_ms = info.get("latency_ms", 0)

        # Record into Prometheus/custom metrics
        record_llm_metrics(prompt_tokens, completion_tokens, latency_ms)

        # Final response text
        return response.choices[0].message.content

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

        # Customer review block
        context_parts.append("\n\n=== CUSTOMER REVIEWS ===")
        for idx, doc in enumerate(documents, 1):
            metadata = doc.get("metadata", {})
            rating = metadata.get("review_rating", "N/A")
            verified = metadata.get("verified_purchase", False)

            context_parts.append(
                f"""
Review {idx}:
Rating: {rating}/5
Verified Purchase: {"Yes" if verified else "No"}
{doc.get("text", "")}
"""
            )

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
