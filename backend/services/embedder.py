from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
from backend.config.settings import EMBEDDING_MODEL_NAME


class EmbeddingService:
    """Service for generating embeddings using sentence transformers."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        """Initialize the embedding model.

        Args:
            model_name: Name of the sentence transformer model to use
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print(f"✓ Embedding model loaded successfully!")
        print(f"  Embedding dimension: {self.model.get_sentence_embedding_dimension()}")

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32, show_progress: bool = True) -> List[List[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once
            show_progress: Whether to show progress bar

        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        return embeddings.tolist()

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors.

        Returns:
            Integer dimension of embeddings
        """
        return self.model.get_sentence_embedding_dimension()


# Singleton instance
_embedder_instance = None


def get_embedder() -> EmbeddingService:
    """Get or create the singleton embedder instance.

    Returns:
        EmbeddingService instance
    """
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = EmbeddingService()
    return _embedder_instance
