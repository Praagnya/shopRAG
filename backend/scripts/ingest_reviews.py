from datasets import load_dataset
import chromadb
from chromadb.config import Settings
from tqdm import tqdm
import uuid
import json
from pathlib import Path

from backend.config.settings import (
    DATASET_NAME,
    SUBSET_REVIEWS,
    SUBSET_META,
    COLLECTION_NAME,
    CHROMA_DB_PATH,
    DATA_DIR,
    MAX_PRODUCTS_TO_LOAD,
    MAX_REVIEWS_PER_PRODUCT,
    MAX_REVIEWS_TO_PROCESS,
    BATCH_SIZE,
    SAVE_CHECKPOINT_EVERY
)
from backend.services.embedder import get_embedder
from backend.utils.text_processor import (
    combine_review_with_product,
    should_include_review
)


def load_product_metadata():
    """Load product metadata and create ASIN -> metadata mapping.

    Returns:
        Dictionary mapping ASIN to product metadata
    """
    print("\n" + "="*80)
    print("LOADING PRODUCT METADATA")
    print("="*80)

    # Load product metadata
    print(f"Downloading product metadata...")
    metadata_dataset = load_dataset(
        DATASET_NAME,
        SUBSET_META,
        split="full",
        streaming=False,  # Download for faster processing
        trust_remote_code=True
    )

    product_cache = {}

    print(f"Loading first {MAX_PRODUCTS_TO_LOAD} products from {len(metadata_dataset)} total...")
    for idx, product in enumerate(tqdm(metadata_dataset, desc="Loading products")):
        asin = product.get('parent_asin')

        if not asin:
            continue

        # Store essential metadata
        product_cache[asin] = {
            'title': product.get('title', 'Unknown Product'),
            'main_category': product.get('main_category', ''),
            'average_rating': product.get('average_rating'),
            'rating_number': product.get('rating_number', 0),
            'price': product.get('price'),
            'features': product.get('features', [])[:5],  # Top 5 features
            'description': product.get('description', [''])[0][:500] if product.get('description') else '',  # First 500 chars
            'store': product.get('store', ''),
        }

        # Stop after loading specified number of products
        if len(product_cache) >= MAX_PRODUCTS_TO_LOAD:
            break

    print(f"Loaded {len(product_cache)} product metadata entries")
    return product_cache


def save_product_cache(product_cache, filepath):
    """Save product cache to JSON file for later use.

    Args:
        product_cache: Dictionary of ASIN -> metadata
        filepath: Path to save JSON file
    """
    print(f"\nSaving product cache to {filepath}...")
    with open(filepath, 'w') as f:
        json.dump(product_cache, f, indent=2)
    print(f"Product cache saved ({len(product_cache)} products)")


def ingest_reviews(product_cache):
    """Load reviews, embed them, and store in ChromaDB.

    Args:
        product_cache: Dictionary mapping ASIN to product metadata
    """
    print("\n" + "="*80)
    print("INGESTING REVIEWS")
    print("="*80)

    # Get set of ASINs we have products for
    valid_asins = set(product_cache.keys())
    print(f"Will process reviews for {len(valid_asins)} products")

    # Initialize embedder
    embedder = get_embedder()

    # Initialize ChromaDB
    print(f"\nInitializing ChromaDB at {CHROMA_DB_PATH}...")
    client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))

    # Delete collection if it exists (fresh start)
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"Deleted existing collection: {COLLECTION_NAME}")
    except:
        pass

    # Create collection
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Amazon Cell Phone & Accessories Reviews"}
    )
    print(f"Created collection: {COLLECTION_NAME}")

    # Load reviews dataset (download full dataset for filtering)
    print(f"\nDownloading reviews from {SUBSET_REVIEWS}...")
    print("This will download ~10-20GB of data (one-time download, cached locally)")
    print("Subsequent runs will use the cached version.\n")

    reviews_dataset = load_dataset(
        DATASET_NAME,
        SUBSET_REVIEWS,
        split="full",
        streaming=False,  # Download full dataset for efficient filtering
        trust_remote_code=True
    )

    print(f"✓ Dataset downloaded! Total reviews in dataset: {len(reviews_dataset)}")

    # Filter to only reviews for our products (MUCH faster than streaming)
    print(f"\nFiltering reviews for {len(valid_asins)} products...")
    reviews_dataset = reviews_dataset.filter(
        lambda x: (x.get('parent_asin') in valid_asins or x.get('asin') in valid_asins),
        desc="Filtering reviews"
    )

    print(f"✓ Found {len(reviews_dataset)} reviews for your {len(valid_asins)} products!")

    # Process reviews in batches
    batch_texts = []
    batch_metadatas = []
    batch_ids = []

    reviews_processed = 0
    reviews_skipped = 0
    reviews_missing_product = 0
    product_review_counts = {}  # Track reviews per product

    print(f"\nProcessing {len(reviews_dataset)} filtered reviews...")
    if MAX_REVIEWS_PER_PRODUCT:
        print(f"(Maximum {MAX_REVIEWS_PER_PRODUCT} reviews per product)")
    if MAX_REVIEWS_TO_PROCESS:
        print(f"(Maximum {MAX_REVIEWS_TO_PROCESS} reviews overall)")
    print(f"Batch size: {BATCH_SIZE}\n")

    for review in tqdm(reviews_dataset, desc="Processing reviews", total=len(reviews_dataset)):
        # Check if we've hit the overall limit
        if MAX_REVIEWS_TO_PROCESS and reviews_processed >= MAX_REVIEWS_TO_PROCESS:
            break

        # Get product ASIN (already filtered, so we know it's in our list)
        asin = review.get('parent_asin') or review.get('asin')

        if not asin:
            continue

        # Check per-product limit
        if MAX_REVIEWS_PER_PRODUCT:
            current_count = product_review_counts.get(asin, 0)
            if current_count >= MAX_REVIEWS_PER_PRODUCT:
                continue

        # Filter low-quality reviews
        if not should_include_review(review):
            reviews_skipped += 1
            continue

        product_metadata = product_cache[asin]

        # Combine review with product info for embedding
        combined_text = combine_review_with_product(review, product_metadata)

        # Prepare metadata to store
        metadata = {
            'asin': asin,
            'product_name': product_metadata['title'],
            'category': product_metadata['main_category'],
            'product_avg_rating': product_metadata['average_rating'] or 0.0,
            'review_rating': float(review.get('rating', 0)),
            'verified_purchase': bool(review.get('verified_purchase', False)),
            'helpful_vote': int(review.get('helpful_vote', 0)),
            'timestamp': int(review.get('timestamp', 0))
        }

        # Add to batch
        batch_texts.append(combined_text)
        batch_metadatas.append(metadata)
        batch_ids.append(str(uuid.uuid4()))

        reviews_processed += 1
        product_review_counts[asin] = product_review_counts.get(asin, 0) + 1

        # Process batch when full
        if len(batch_texts) >= BATCH_SIZE:
            # Generate embeddings
            embeddings = embedder.embed_batch(batch_texts, show_progress=False)

            # Add to ChromaDB
            collection.add(
                embeddings=embeddings,
                documents=batch_texts,
                metadatas=batch_metadatas,
                ids=batch_ids
            )

            # Clear batch
            batch_texts = []
            batch_metadatas = []
            batch_ids = []

            # Save checkpoint periodically
            if reviews_processed % SAVE_CHECKPOINT_EVERY == 0:
                print(f"\n[Checkpoint] Processed {reviews_processed} reviews so far...")
                print(f"  Products with reviews: {len(product_review_counts)}")
                print(f"  Total in ChromaDB: {collection.count()}")

    # Process remaining reviews in batch
    if batch_texts:
        print("\nProcessing final batch...")
        embeddings = embedder.embed_batch(batch_texts, show_progress=True)
        collection.add(
            embeddings=embeddings,
            documents=batch_texts,
            metadatas=batch_metadatas,
            ids=batch_ids
        )

    # Print statistics
    print("\n" + "="*80)
    print("INGESTION COMPLETE!")
    print("="*80)
    print(f"Products loaded: {len(valid_asins)}")
    print(f"Products with reviews: {len(product_review_counts)}")
    print(f"Reviews successfully embedded: {reviews_processed}")
    print(f"  Reviews skipped (low quality): {reviews_skipped}")
    print(f"  Average reviews per product: {reviews_processed / len(product_review_counts) if product_review_counts else 0:.1f}")
    print(f"  Total documents in ChromaDB: {collection.count()}")
    print("="*80)


def main():
    """Main ingestion pipeline."""
    print("\n" + "="*80)
    print("AMAZON REVIEWS INGESTION PIPELINE")
    print("Cell Phones & Accessories Dataset")
    print("="*80)

    # Step 1: Load product metadata
    product_cache = load_product_metadata()

    # Step 2: Save product cache for later use
    cache_filepath = DATA_DIR / "product_cache.json"
    save_product_cache(product_cache, cache_filepath)

    # Step 3: Ingest reviews for those products
    ingest_reviews(product_cache)

    print("\nAll done! Your RAG database is ready!")
    print(f"   ChromaDB location: {CHROMA_DB_PATH}")
    print(f"   Product cache: {cache_filepath}")


if __name__ == "__main__":
    main()
