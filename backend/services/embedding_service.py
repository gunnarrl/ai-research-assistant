from sentence_transformers import SentenceTransformer

# 1. Initialize the embedding model.
# The model 'all-MiniLM-L6-v2' is a great starting point: it's fast, efficient,
# and produces 384-dimensional embeddings, matching what we defined in our database model.
# The first time this line runs, it will download the model from the internet.
model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generates vector embeddings for a list of text chunks.

    Args:
        texts: A list of strings to be embedded.

    Returns:
        A list of vector embeddings, where each embedding is a list of floats.
    """
    # The model.encode() method efficiently converts a list of texts into embeddings.
    embeddings = model.encode(texts)
    
    # Convert the numpy arrays to lists of floats for database compatibility.
    return [embedding.tolist() for embedding in embeddings]

# --- Testing Block ---
if __name__ == '__main__':
    sample_texts = [
        "This is the first sentence to be embedded.",
        "Here is a second piece of text.",
        "Vector embeddings represent text in a numerical format."
    ]
    
    print("Generating embeddings for the following texts:")
    for text in sample_texts:
        print(f"- {text}")
        
    # Generate the embeddings
    vectors = generate_embeddings(sample_texts)
    
    print("\n--- Results ---")
    print(f"Successfully generated {len(vectors)} vectors.")
    
    # Print the details of the first vector to verify
    if vectors:
        print(f"Dimension of the first vector: {len(vectors[0])}")
        print(f"First 5 values of the first vector: {vectors[0][:5]}")