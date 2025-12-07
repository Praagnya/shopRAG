"""
Ingest Amazon reviews into PostgreSQL with pgvector embeddings.
"""

from datasets import load_dataset
import psycopg2
from psycopg2.extras import execute_batch
from tqdm import tqdm
import json
from pathlib import Path
import os
from dotenv import load_dotenv

from backend.config.settings import (
    DATASET_NAME,
    SUBSET_REVIEWS,
    SUBSET_META,
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

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def load_product_metadata():
    """Load product metadata and create ASIN -> metadata mapping."""
    print("\n" + "="*80)
    print("LOADING PRODUCT METADATA")
    print("="*80)

    # Load product metadata
    print(f"Downloading product metadata...")
    metadata_dataset = load_dataset(
        DATASET_NAME,
        SUBSET_META,
        split="full",
        streaming=False,
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
            'features': product.get('features', [])[:5],
            'description': product.get('description', [''])[0][:500] if product.get('description') else '',
            'store': product.get('store', ''),
        }

        if len(product_cache) >= MAX_PRODUCTS_TO_LOAD:
            break

    print(f"Loaded {len(product_cache)} product metadata entries")
    return product_cache


def save_product_cache(product_cache, filepath):
    """Save product cache to JSON file."""
    print(f"\nSaving product cache to {filepath}...")
    with open(filepath, 'w') as f:
        json.dump(product_cache, f, indent=2)
    print(f"Product cache saved ({len(product_cache)} products)")


def insert_products_to_db(product_cache, conn):
    """Insert products into PostgreSQL."""
    print("\nInserting products into PostgreSQL...")
    cursor = conn.cursor()

    products_data = []
    for asin, product in product_cache.items():
        products_data.append((
            asin,
            product['title'],
            product['main_category'],
            product['average_rating'],
            product['rating_number'],
            str(product.get('price', '')),
            json.dumps(product['features']),
            product['description'],
            product['store']
        ))

    execute_batch(cursor, """
        INSERT INTO products (asin, title, main_category, average_rating, rating_number,
                            price, features, description, store)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (asin) DO NOTHING
    """, products_data, page_size=100)

    conn.commit()
    cursor.close()
    print(f"✓ Inserted {len(products_data)} products into database")


def ingest_reviews(product_cache, conn):
    """Load reviews, embed them, and store in PostgreSQL."""
    print("\n" + "="*80)
    print("INGESTING REVIEWS")
    print("="*80)

    valid_asins = set(product_cache.keys())
    print(f"Will process reviews for {len(valid_asins)} products")

    # Initialize embedder
    embedder = get_embedder()

    # Load reviews dataset
    print(f"\nDownloading reviews from {SUBSET_REVIEWS}...")
    print("This will download ~10-20GB of data (one-time download, cached locally)")
    print("Subsequent runs will use the cached version.\n")

    reviews_dataset = load_dataset(
        DATASET_NAME,
        SUBSET_REVIEWS,
        split="full",
        streaming=False,
        trust_remote_code=True
    )

    print(f"✓ Dataset downloaded! Total reviews in dataset: {len(reviews_dataset)}")

    # Filter to only reviews for our products
    print(f"\nFiltering reviews for {len(valid_asins)} products...")
    reviews_dataset = reviews_dataset.filter(
        lambda x: (x.get('parent_asin') in valid_asins or x.get('asin') in valid_asins),
        desc="Filtering reviews"
    )

    print(f"✓ Found {len(reviews_dataset)} reviews for your {len(valid_asins)} products!")

    # Process reviews in batches
    batch_texts = []
    batch_data = []

    reviews_processed = 0
    reviews_skipped = 0
    product_review_counts = {}

    cursor = conn.cursor()

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

        # Get product ASIN
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

        # Prepare data tuple for insertion
        review_data = (
            asin,
            product_metadata['title'],
            product_metadata['main_category'],
            product_metadata['average_rating'],
            float(review.get('rating', 0)),
            bool(review.get('verified_purchase', False)),
            int(review.get('helpful_vote', 0)),
            int(review.get('timestamp', 0)),
            combined_text
        )

        # Add to batch
        batch_texts.append(combined_text)
        batch_data.append(review_data)

        reviews_processed += 1
        product_review_counts[asin] = product_review_counts.get(asin, 0) + 1

        # Process batch when full
        if len(batch_texts) >= BATCH_SIZE:
            # Generate embeddings
            embeddings = embedder.embed_batch(batch_texts, show_progress=False)

            # Prepare data with embeddings
            batch_with_embeddings = [
                data + (embeddings[i],) for i, data in enumerate(batch_data)
            ]

            # Insert into PostgreSQL
            execute_batch(cursor, """
                INSERT INTO reviews (asin, product_name, category, product_avg_rating,
                                   review_rating, verified_purchase, helpful_vote,
                                   timestamp, review_text, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch_with_embeddings, page_size=100)

            conn.commit()

            # Clear batch
            batch_texts = []
            batch_data = []

            # Save checkpoint
            if reviews_processed % SAVE_CHECKPOINT_EVERY == 0:
                print(f"\n[Checkpoint] Processed {reviews_processed} reviews so far...")
                print(f"  Products with reviews: {len(product_review_counts)}")
                cursor.execute("SELECT COUNT(*) FROM reviews")
                count = cursor.fetchone()[0]
                print(f"  Total in PostgreSQL: {count}")

    # Process remaining reviews in batch
    if batch_texts:
        print("\nProcessing final batch...")
        embeddings = embedder.embed_batch(batch_texts, show_progress=True)

        batch_with_embeddings = [
            data + (embeddings[i],) for i, data in enumerate(batch_data)
        ]

        execute_batch(cursor, """
            INSERT INTO reviews (asin, product_name, category, product_avg_rating,
                               review_rating, verified_purchase, helpful_vote,
                               timestamp, review_text, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch_with_embeddings, page_size=100)

        conn.commit()

    # Print statistics
    cursor.execute("SELECT COUNT(*) FROM reviews")
    total_reviews = cursor.fetchone()[0]

    cursor.close()

    print("\n" + "="*80)
    print("INGESTION COMPLETE!")
    print("="*80)
    print(f"Products loaded: {len(valid_asins)}")
    print(f"Products with reviews: {len(product_review_counts)}")
    print(f"Reviews successfully embedded: {reviews_processed}")
    print(f"  Reviews skipped (low quality): {reviews_skipped}")
    print(f"  Average reviews per product: {reviews_processed / len(product_review_counts) if product_review_counts else 0:.1f}")
    print(f"  Total documents in PostgreSQL: {total_reviews}")
    print("="*80)


def main():
    """Main ingestion pipeline."""
    print("\n" + "="*80)
    print("AMAZON REVIEWS INGESTION PIPELINE - PostgreSQL + pgvector")
    print("Cell Phones & Accessories Dataset")
    print("="*80)

    # Connect to PostgreSQL
    print(f"\nConnecting to PostgreSQL...")
    conn = psycopg2.connect(DATABASE_URL)
    print("✓ Connected to PostgreSQL")

    # Step 1: Load product metadata
    product_cache = load_product_metadata()

    # Step 2: Save product cache for later use
    cache_filepath = DATA_DIR / "product_cache.json"
    save_product_cache(product_cache, cache_filepath)

    # Step 3: Insert products into PostgreSQL
    insert_products_to_db(product_cache, conn)

    # Step 4: Ingest reviews
    ingest_reviews(product_cache, conn)

    conn.close()

    print("\nAll done! Your PostgreSQL RAG database is ready!")
    print(f"   Database: PostgreSQL + pgvector")
    print(f"   Product cache: {cache_filepath}")


if __name__ == "__main__":
    main()
