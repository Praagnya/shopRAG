"""
Simple test script to verify RAG pipeline is working.
Run this after ingestion to test the system before starting the API.
"""

from backend.services.rag_pipeline import get_rag_pipeline
import os

def main():
    print("\n" + "="*80)
    print("TESTING RAG PIPELINE")
    print("="*80)

    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("\nWARNING: OPENAI_API_KEY environment variable not set!")
        print("Please set it first:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        return

    # Initialize pipeline
    print("\nInitializing RAG pipeline...")
    try:
        pipeline = get_rag_pipeline()
    except Exception as e:
        print(f"\nError initializing pipeline: {e}")
        print("\nMake sure you've run the ingestion pipeline first:")
        print("  python backend/scripts/ingest_reviews.py")
        return

    # Check status
    print("\n" + "-"*80)
    print("Pipeline Status:")
    print("-"*80)
    status = pipeline.get_pipeline_status()
    print(f"Status: {status['status']}")
    print(f"Number of products in cache: {status['num_products']}")
    print(f"Embedding dimension: {status['embedding_dimension']}")
    print(f"Documents in vector DB: {status['vector_db']['count']}")
    print(f"LLM model: {status['llm_model']}")

    # Test queries
    test_queries = [
        "What do customers say about battery life?",
        "Are there any complaints about the cameras?",
        "How is the build quality?"
    ]

    for i, query in enumerate(test_queries, 1):
        print("\n" + "="*80)
        print(f"TEST QUERY {i}: {query}")
        print("="*80)

        try:
            result = pipeline.query(query, top_k=3)

            print(f"\nProduct: {result['product_metadata'].get('title', 'Unknown')}")
            print(f"Retrieved {result['num_documents_used']} reviews")
            print(f"\nRESPONSE:")
            print("-"*80)
            print(result['response'])
            print("-"*80)

        except Exception as e:
            print(f"Error processing query: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("RAG PIPELINE TEST COMPLETE!")
    print("="*80)
    print("\nIf all tests passed, you can now start the API server:")
    print("  python backend/api/main.py")
    print("  or")
    print("  uvicorn backend.api.main:app --reload")
    print("\n")


if __name__ == "__main__":
    main()
