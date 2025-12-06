from datasets import load_dataset
from sentence_transformers import SentenceTransformer 
import chromadb 
from tqdm import tqdm 
import uuid 

# 
# Configuration 
# 

DATASET_NAME = "McAuley-Lab/Amazon-Reviews-2023"
SUBSET_REVIEWS = "raw_review_Cell_Phones_and_Accessories"
SUBSET_META = "raw_meta_Cell_Phones_and_Accessories"
COLLECTION_NAME = "cellphone_reviews"

# Load the reviews dataset with streaming for large datasets
print(f"Loading {SUBSET_REVIEWS} dataset...")
reviews_dataset = load_dataset(
    DATASET_NAME,
    SUBSET_REVIEWS,
    split="full",
    streaming=True,
    trust_remote_code=True
)

print(f"Reviews dataset loaded successfully!")
print(f"Taking a look at the first review example:")

# Peek at first review example
for idx, example in enumerate(reviews_dataset):
    print("Review example:")
    print(example)
    if idx == 0:  # Just show first one
        break

# Load metadata to get product names
print("\n" + "="*50)
print("Loading metadata to get product information...")
print("="*50 + "\n")

metadata = load_dataset(
    DATASET_NAME,
    SUBSET_META,
    split="full",
    streaming=True,
    trust_remote_code=True
)

# Show several product description examples
print("Product description examples:\n")
for idx, example in enumerate(metadata):
    print(f"Example {idx + 1}:")
    print(f"Product: {example.get('title', 'N/A')}")
    print(f"Description: {example.get('description', ['N/A'])}")
    print(f"Store: {example.get('store', 'N/A')}")
    print("-" * 80)

    if idx >= 4:  # Show 5 examples
        break
