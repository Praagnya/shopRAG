from sentence_transformers import SentenceTransformer  # existing
from typing import List, Union
import numpy as np
import os  # ADDED
from backend.config.settings import EMBEDDING_MODEL_NAME


# --------------------------------------------------------------
# ADDED FOR VERSION A MOCK MODE (lightweight dummy embeddings)
# --------------------------------------------------------------

class MockEmbeddingService:
    """
    Lightweight mock embedder used in Version A.
    Does NOT load any transformer model.
    """

    def __init__(self):
        print("⚠ Using MOCK EmbeddingService (Version A). No real embeddings generated.")
        self.dim = 384  # safe small dimension

    def embed_text(self, text: str) -> List[float]:
        """Return a fixed dummy vector."""
        return [0.01] * self.dim

    def embed_batch(self, texts: List[str], batch_size: int = 32, show_progress: bool = False) -> List[List[float]]:
        """Return a batch of dummy vectors."""
        return [[0.01] * self.dim for _ in texts]

    def get_embedding_dimension(self) -> int:
        return self.dim


# --------------------------------------------------------------
# ORIGINAL EMBEDDING SERVICE (unchanged)
# --------------------------------------------------------------

class EmbeddingService:
    """Service for generating embeddings using sentence transformers."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        """Initialize the embedding model.

        Args:
            model_name: Name of the sentence transformer model to use
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print(f"Embedding model loaded successfully!")
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


# --------------------------------------------------------------
# SINGLETON FACTORY — CHOOSES MOCK OR REAL EMBEDDER
# --------------------------------------------------------------

_embedder_instance = None


def get_embedder():
    """
    Get or create the embedder.

    VERSION A → Uses mock embedder if RAG_MODE=MOCK
    VERSION B → Uses full SentenceTransformer embedder
    """
    global _embedder_instance

    if _embedder_instance is None:

        rag_mode = os.getenv("RAG_MODE", "FULL").upper()

        if rag_mode == "MOCK":
            print("🔧 RAG_MODE=MOCK → Using MockEmbeddingService")
            _embedder_instance = MockEmbeddingService()
        else:
            _embedder_instance = EmbeddingService()

    return _embedder_instance
