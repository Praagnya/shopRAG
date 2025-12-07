from datasets import load_dataset
import pandas as pd
from collections import Counter

DATASET_NAME = "McAuley-Lab/Amazon-Reviews-2023"
SUBSET_REVIEWS = "raw_review_Cell_Phones_and_Accessories"
SUBSET_META = "raw_meta_Cell_Phones_and_Accessories"

print("="*80)
print("EXPLORATORY DATA ANALYSIS: Cell Phones & Accessories")
print("="*80)

# Load reviews dataset
print("\n[1] Loading Reviews Dataset...")
reviews_dataset = load_dataset(
    DATASET_NAME,
    SUBSET_REVIEWS,
    split="full",
    streaming=True,
    trust_remote_code=True
)

# Analyze first 1000 reviews
print("[2] Analyzing first 1000 reviews...\n")

sample_size = 1000
reviews_sample = []
ratings = []
text_lengths = []
has_title_count = 0
has_text_count = 0
verified_purchase_count = 0
has_images_count = 0

for idx, review in enumerate(reviews_dataset):
    if idx >= sample_size:
        break

    reviews_sample.append(review)

    # Collect statistics
    if 'rating' in review and review['rating']:
        ratings.append(review['rating'])

    if 'text' in review and review['text']:
        has_text_count += 1
        text_lengths.append(len(review['text']))

    if 'title' in review and review['title']:
        has_title_count += 1

    if 'verified_purchase' in review and review['verified_purchase']:
        verified_purchase_count += 1

    if 'images' in review and review['images']:
        has_images_count += 1

print(f"✓ Analyzed {len(reviews_sample)} reviews\n")

# Print sample review structure
print("="*80)
print("SAMPLE REVIEW STRUCTURE")
print("="*80)
if reviews_sample:
    first_review = reviews_sample[0]
    print(f"\nFields available: {list(first_review.keys())}\n")
    print("First Review Example:")
    print("-" * 80)
    for key, value in first_review.items():
        if isinstance(value, str) and len(value) > 100:
            print(f"{key}: {value[:100]}...")
        else:
            print(f"{key}: {value}")

# Statistics
print("\n" + "="*80)
print("REVIEW STATISTICS")
print("="*80)
print(f"\nTotal reviews analyzed: {len(reviews_sample)}")
print(f"Reviews with text: {has_text_count} ({has_text_count/len(reviews_sample)*100:.1f}%)")
print(f"Reviews with title: {has_title_count} ({has_title_count/len(reviews_sample)*100:.1f}%)")
print(f"Verified purchases: {verified_purchase_count} ({verified_purchase_count/len(reviews_sample)*100:.1f}%)")
print(f"Reviews with images: {has_images_count} ({has_images_count/len(reviews_sample)*100:.1f}%)")

# Rating distribution
if ratings:
    print(f"\n--- Rating Distribution ---")
    rating_counts = Counter(ratings)
    for rating in sorted(rating_counts.keys(), reverse=True):
        count = rating_counts[rating]
        bar = "█" * int(count/len(ratings) * 50)
        print(f"{rating:.1f} ⭐: {count:4d} ({count/len(ratings)*100:5.1f}%) {bar}")
    print(f"Average rating: {sum(ratings)/len(ratings):.2f}")

# Text length statistics
if text_lengths:
    print(f"\n--- Review Text Length ---")
    print(f"Min length: {min(text_lengths)} chars")
    print(f"Max length: {max(text_lengths)} chars")
    print(f"Average length: {sum(text_lengths)/len(text_lengths):.0f} chars")
    print(f"Median length: {sorted(text_lengths)[len(text_lengths)//2]} chars")

# Load metadata
print("\n" + "="*80)
print("PRODUCT METADATA ANALYSIS")
print("="*80)

metadata_dataset = load_dataset(
    DATASET_NAME,
    SUBSET_META,
    split="full",
    streaming=True,
    trust_remote_code=True
)

print("\n[3] Analyzing first 100 product metadata entries...\n")

meta_sample = []
has_description_count = 0
has_features_count = 0
has_price_count = 0
categories_list = []

for idx, meta in enumerate(metadata_dataset):
    if idx >= 100:
        break

    meta_sample.append(meta)

    if 'description' in meta and meta['description']:
        has_description_count += 1

    if 'features' in meta and meta['features']:
        has_features_count += 1

    if 'price' in meta and meta['price']:
        has_price_count += 1

    if 'main_category' in meta and meta['main_category']:
        categories_list.append(meta['main_category'])

print(f"✓ Analyzed {len(meta_sample)} product metadata entries\n")

# Print sample metadata structure
print("="*80)
print("SAMPLE PRODUCT METADATA STRUCTURE")
print("="*80)
if meta_sample:
    first_meta = meta_sample[0]
    print(f"\nFields available: {list(first_meta.keys())}\n")
    print("First Product Example:")
    print("-" * 80)
    for key, value in first_meta.items():
        if isinstance(value, str) and len(value) > 100:
            print(f"{key}: {value[:100]}...")
        elif isinstance(value, list) and len(str(value)) > 100:
            print(f"{key}: {str(value)[:100]}...")
        else:
            print(f"{key}: {value}")

# Metadata statistics
print("\n" + "="*80)
print("METADATA STATISTICS")
print("="*80)
print(f"\nTotal products analyzed: {len(meta_sample)}")
print(f"Products with description: {has_description_count} ({has_description_count/len(meta_sample)*100:.1f}%)")
print(f"Products with features: {has_features_count} ({has_features_count/len(meta_sample)*100:.1f}%)")
print(f"Products with price: {has_price_count} ({has_price_count/len(meta_sample)*100:.1f}%)")

if categories_list:
    print(f"\n--- Categories ---")
    cat_counts = Counter(categories_list)
    for cat, count in cat_counts.most_common(10):
        print(f"  {cat}: {count}")

print("\n" + "="*80)
print("KEY INSIGHTS FOR RAG SYSTEM")
print("="*80)
print("""
1. Review Fields to Use for Embedding:
   - rating (combine with text for context)
   - title (good summary)
   - text (main content)
   - verified_purchase (quality signal)

2. Metadata Fields to Join:
   - title (product name)
   - description
   - features
   - main_category

3. Preprocessing Needed:
   - Handle missing text/title fields
   - Combine rating + title + text for rich context
   - Filter out very short reviews (< 20 chars)
   - Clean HTML/special characters

4. ChromaDB Metadata to Store:
   - rating
   - asin (product ID)
   - verified_purchase
   - helpful_vote
   - timestamp
""")

print("="*80)
print("EDA COMPLETE!")
print("="*80)
