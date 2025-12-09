"""
Gradio Chat UI for shopRAG - Product Review Chatbot
"""

import gradio as gr
import json
from pathlib import Path
import sys

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.rag_pipeline import get_rag_pipeline


# Load products at startup
def load_products():
    """Load product cache from JSON file."""
    cache_path = Path(__file__).parent.parent / "data" / "product_cache.json"

    if not cache_path.exists():
        return {}

    with open(cache_path, 'r') as f:
        products = json.load(f)

    return products


# Initialize RAG pipeline
print("Loading RAG Pipeline...")
rag_pipeline = get_rag_pipeline()
products_cache = load_products()
print(f"✓ Loaded {len(products_cache)} products")


def extract_asin_from_choice(choice):
    """Extract ASIN from input (now expects direct ASIN or empty string)."""
    if not choice or choice.strip() == "":
        return None
    # Return the ASIN directly (user types it in)
    return choice.strip()


def format_product_info(product_metadata):
    """Format product metadata as markdown."""
    if not product_metadata:
        return "No product selected"

    info = f"""
### 📦 {product_metadata.get('title', 'Unknown Product')}

**Category:** {product_metadata.get('main_category', 'N/A')}
**Average Rating:** {'⭐' * int(product_metadata.get('average_rating', 0))} {product_metadata.get('average_rating', 'N/A')}/5
**Price:** ${product_metadata.get('price', 'N/A')}
**Reviews:** {product_metadata.get('rating_number', 0)}

**Key Features:**
"""

    features = product_metadata.get('features', [])
    if features:
        for feature in features[:5]:
            info += f"- {feature}\n"
    else:
        info += "- No features listed\n"

    return info


def chat_function(message, history, selected_product, top_k):
    """
    Process user message and return response.

    Args:
        message: User's question
        history: Chat history
        selected_product: Selected product from dropdown
        top_k: Number of reviews to retrieve

    Returns:
        Updated chat history and product info
    """
    if not message.strip():
        return history, ""

    # Extract ASIN from dropdown
    product_asin = extract_asin_from_choice(selected_product)

    # Query the RAG pipeline
    try:
        result = rag_pipeline.query(
            message,
            top_k=top_k,
            product_asin=product_asin
        )

        # Format response with sources
        response = result['response']

        # Add sources info
        num_docs = result['num_documents_used']
        response += f"\n\n---\n*Based on {num_docs} customer review(s)*"

        # Convert history to list format if needed
        if history is None:
            history = []
        
        # Gradio 6.0.2 Chatbot expects list of dictionaries with 'role' and 'content'
        # Convert existing history to dict format if needed
        formatted_history = []
        for item in history:
            if isinstance(item, dict) and 'role' in item:
                formatted_history.append(item)
            elif isinstance(item, tuple) and len(item) == 2:
                # Convert tuple (user, bot) to dict format
                formatted_history.append({"role": "user", "content": item[0]})
                formatted_history.append({"role": "assistant", "content": item[1]})
            elif isinstance(item, list) and len(item) == 2:
                # Handle list format
                formatted_history.append({"role": "user", "content": item[0]})
                formatted_history.append({"role": "assistant", "content": item[1]})
        
        # Add new message and response
        formatted_history.append({"role": "user", "content": message})
        formatted_history.append({"role": "assistant", "content": response})

        # Format product info
        product_info = format_product_info(result.get('product_metadata'))

        return formatted_history, product_info

    except ValueError as e:
        # Guardrail validation errors - user-friendly messages
        error_str = str(e).replace('Invalid query: ', '')

        # Customize messages based on error type
        if "too long" in error_str.lower():
            error_msg = "Sorry, your query is too long. Please keep it under 500 characters."
        elif "too short" in error_str.lower():
            error_msg = "Sorry, your query is too short. Please provide at least 3 characters."
        elif "empty" in error_str.lower():
            error_msg = "Please enter a question to continue."
        elif "rate limit" in error_str.lower():
            error_msg = "Too many requests. Please wait a moment before trying again."
        else:
            error_msg = f"Unable to process your query. Please try rephrasing."

        if history is None:
            history = []

        # Convert history to dict format
        formatted_history = []
        for item in history:
            if isinstance(item, dict) and 'role' in item:
                formatted_history.append(item)
            elif isinstance(item, tuple) and len(item) == 2:
                formatted_history.append({"role": "user", "content": item[0]})
                formatted_history.append({"role": "assistant", "content": item[1]})
            elif isinstance(item, list) and len(item) == 2:
                formatted_history.append({"role": "user", "content": item[0]})
                formatted_history.append({"role": "assistant", "content": item[1]})

        formatted_history.append({"role": "user", "content": message})
        formatted_history.append({"role": "assistant", "content": error_msg})
        return formatted_history, ""

    except Exception as e:
        # Other errors
        error_msg = f"An error occurred while processing your request. Please try again."
        if history is None:
            history = []

        # Convert history to dict format
        formatted_history = []
        for item in history:
            if isinstance(item, dict) and 'role' in item:
                formatted_history.append(item)
            elif isinstance(item, tuple) and len(item) == 2:
                formatted_history.append({"role": "user", "content": item[0]})
                formatted_history.append({"role": "assistant", "content": item[1]})
            elif isinstance(item, list) and len(item) == 2:
                formatted_history.append({"role": "user", "content": item[0]})
                formatted_history.append({"role": "assistant", "content": item[1]})

        formatted_history.append({"role": "user", "content": message})
        formatted_history.append({"role": "assistant", "content": error_msg})
        return formatted_history, ""


# Create Gradio Interface
with gr.Blocks(title="shopRAG - Product Review Chatbot") as demo:
    gr.Markdown(
        f"""
        # 🛍️ shopRAG - Product Review Chatbot
        Ask questions about product reviews and get AI-powered answers!

        **Database:** {len(products_cache):,} products with 170k+ reviews
        """
    )

    with gr.Row():
        # Left column: Chat interface
        with gr.Column(scale=2):
            # Product selector - using Textbox instead of Dropdown for 10k products
            product_dropdown = gr.Textbox(
                value="",
                label="📦 Product ASIN (optional)",
                placeholder="Enter product ASIN to filter to specific product, or leave empty to search all products",
                info="Example: B07XYZ1234"
            )

            # Top-k slider
            top_k_slider = gr.Slider(
                minimum=1,
                maximum=10,
                value=5,
                step=1,
                label="Number of reviews to analyze",
                info="More reviews = more context but slower response"
            )

            # Chat interface
            chatbot = gr.Chatbot(
                height=400,
                label="💬 Chat"
            )

            # Message input
            msg = gr.Textbox(
                label="Your Question",
                placeholder="Ask me anything about the product reviews! (e.g., 'How is the quality?', 'Is it durable?')",
                lines=2
            )

            with gr.Row():
                submit_btn = gr.Button("Send 🚀", variant="primary")
                clear_btn = gr.Button("Clear Chat 🗑️")

        # Right column: Product info
        with gr.Column(scale=1):
            product_info = gr.Markdown("### Select a product to see details")

    # Example questions and ASINs
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 💡 Example Questions:")
            gr.Examples(
                examples=[
                    "How is the quality of this case?",
                    "Is it worth the price?",
                    "Do customers complain about durability?",
                    "How well does it protect the phone?",
                    "What do people say about the material?",
                    "Are there any issues with the fit?",
                ],
                inputs=msg,
                label="Click to try:"
            )
        with gr.Column():
            # Show example ASINs (verified to have reviews in database)
            example_asins = ['B07SKQZSN6', 'B0C14LLH14', 'B077ZNJ6XX', 'B0C26XD5J2', 'B0C147N71M']
            example_list = []
            for asin in example_asins:
                if asin in products_cache:
                    title = products_cache[asin]['title'][:50]
                    reviews = products_cache[asin].get('rating_number', 0)
                    example_list.append(f"- `{asin}`: {title}... ({reviews:,} reviews)")
            gr.Markdown(f"### 📦 Example Product ASINs:\n" + "\n".join(example_list) + "\n\n*Leave ASIN blank to search all products*")

    # Event handlers
    submit_btn.click(
        chat_function,
        inputs=[msg, chatbot, product_dropdown, top_k_slider],
        outputs=[chatbot, product_info]
    ).then(
        lambda: "",  # Clear input after sending
        None,
        msg
    )

    msg.submit(
        chat_function,
        inputs=[msg, chatbot, product_dropdown, top_k_slider],
        outputs=[chatbot, product_info]
    ).then(
        lambda: "",  # Clear input after sending
        None,
        msg
    )

    clear_btn.click(lambda: ([], ""), None, [chatbot, product_info])

    # Update product info when ASIN is entered
    product_dropdown.change(
        lambda asin_input: format_product_info(
            products_cache.get(asin_input.strip(), {})
        ) if asin_input.strip() and asin_input.strip() in products_cache else "### All Products\nSearching across all available products." if not asin_input.strip() else f"### Product Not Found\nASIN '{asin_input.strip()}' not found in database.",
        inputs=product_dropdown,
        outputs=product_info
    )


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 Starting shopRAG Gradio Interface...")
    print("="*80)
    demo.launch(
        server_name="0.0.0.0",  # Allow external connections
        server_port=7860,
        share=True,  # Create public Gradio share link
        show_error=True
    )
