import os
from pathlib import Path
from dotenv import load_dotenv

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')
DATA_DIR = BASE_DIR / "data"
CHROMA_DB_PATH = DATA_DIR / "chroma_db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DB_PATH.mkdir(exist_ok=True)

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"  # or "gpt-4o"

# Embedding Configuration
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# ChromaDB Configuration
COLLECTION_NAME = "amazon_reviews"

# RAG Configuration
TOP_K_RESULTS = 5
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]

# Dataset Configuration
DATASET_NAME = "McAuley-Lab/Amazon-Reviews-2023"
SUBSET_REVIEWS = "raw_review_Cell_Phones_and_Accessories"
SUBSET_META = "raw_meta_Cell_Phones_and_Accessories"

# Ingestion limits
MAX_PRODUCTS_TO_LOAD = 50000
MAX_REVIEWS_PER_PRODUCT = 100
MAX_REVIEWS_TO_PROCESS = None

# Ingestion Performance
BATCH_SIZE = 512
SAVE_CHECKPOINT_EVERY = 1000

# Logging
LOG_LEVEL = "INFO"

# -----------------------
# NEW — RAG Runtime Modes
# -----------------------

# Version A vs Version B
RAG_MODE = os.getenv("RAG_MODE", "FULL").upper()

# Retriever selection
RETRIEVER_MODE = os.getenv("RETRIEVER_MODE", "postgres").lower()
