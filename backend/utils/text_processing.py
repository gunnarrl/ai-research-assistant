# backend/utils/text_processing.py
import re
import numpy as np
import nltk
from sentence_transformers import SentenceTransformer

# --- Fallback Function for very long sentences ---
def _chunk_long_sentence(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Splits a single long text string into smaller, word-aware chunks.
    This is a helper for the main hybrid chunker.
    """

    text = text.replace('\x00', '')

    if not isinstance(text, str) or chunk_overlap >= chunk_size:
        return []

    chunks = []
    start_index = 0
    
    while start_index < len(text):
        end_index = start_index + chunk_size
        if end_index >= len(text):
            chunks.append(text[start_index:])
            break
        
        # Find the last space to avoid splitting words
        split_index = text.rfind(' ', start_index, end_index)
        if split_index == -1: # No space found, hard cut
            split_index = end_index
            
        chunks.append(text[start_index:split_index])
        start_index = split_index - chunk_overlap
        
        # Ensure we don't get stuck
        if start_index < 0:
            start_index = split_index

    return chunks

# --- Main Hybrid Chunking Function ---
def chunk_text(
    text: str, 
    model: SentenceTransformer, 
    similarity_threshold: float = 0.5,
    sentence_overlap: int = 1,
    max_sentence_chars: int = 1000,
    fallback_chunk_size: int = 400,
    fallback_chunk_overlap: int = 100
) -> list[str]:
    """
    Splits a long text into semantically coherent chunks using a hybrid approach.

    Args:
        text: The input text to be chunked.
        model: The SentenceTransformer model for embeddings.
        similarity_threshold: Lower values -> fewer, larger chunks. Higher values -> more, smaller chunks.
        sentence_overlap: Number of sentences to overlap between chunks for context.
        max_sentence_chars: Sentences longer than this will be split by the fallback method.
        fallback_chunk_size: The chunk size for the fixed-size fallback chunker.
        fallback_chunk_overlap: The overlap for the fixed-size fallback chunker.

    Returns:
        A list of semantically coherent text chunks.
    """

    text = text.replace('\x00', '')


    # 1. Split text into sentences using NLTK for better accuracy
    try:
        base_sentences = nltk.sent_tokenize(text)
    except LookupError:
        print("NLTK 'punkt' tokenizer not found. Downloading...")
        nltk.download('punkt')
        base_sentences = nltk.sent_tokenize(text)

    # 2. Handle very long sentences using the fallback chunker (Hybrid Approach)
    processed_sentences = []
    for sentence in base_sentences:
        if len(sentence) > max_sentence_chars:
            processed_sentences.extend(_chunk_long_sentence(
                sentence, fallback_chunk_size, fallback_chunk_overlap
            ))
        else:
            processed_sentences.append(sentence)
    
    if not processed_sentences:
        return []

    # 3. Generate embeddings for each processed sentence/chunk
    embeddings = model.encode(processed_sentences, convert_to_tensor=True)

    # 4. Calculate cosine similarity between adjacent items
    similarities = []
    for i in range(len(processed_sentences) - 1):
        emb1 = embeddings[i]
        emb2 = embeddings[i+1]
        similarity = np.dot(emb1.cpu().numpy(), emb2.cpu().numpy()) / \
                     (np.linalg.norm(emb1.cpu().numpy()) * np.linalg.norm(emb2.cpu().numpy()))
        similarities.append(similarity)

    # 5. Identify split points
    split_indices = [i + 1 for i, sim in enumerate(similarities) if sim < similarity_threshold]

    # 6. Group sentences into chunks with overlap
    chunks = []
    start_index = 0
    for end_index in split_indices:
        # Ensure overlap doesn't go below zero
        overlap_start = max(0, start_index - sentence_overlap)
        chunk = " ".join(processed_sentences[overlap_start:end_index])
        chunks.append(chunk)
        start_index = end_index

    # Add the final chunk
    overlap_start = max(0, start_index - sentence_overlap)
    final_chunk = " ".join(processed_sentences[overlap_start:])
    chunks.append(final_chunk.strip())

    return [chunk for chunk in chunks if chunk] # Filter out any empty chunks

# --- Testing Block ---
if __name__ == '__main__':
    sample_text = """This is a long sample text. The purpose is to demonstrate chunking. Dr. Smith lives on St. John's St. A completely different topic now follows. The solar system has eight planets. Jupiter is the largest. Now, an extremely long sentence to test the fallback mechanism: this single sentence will go on and on, far exceeding the character limit we have set, forcing the hybrid chunker to switch from its semantic, sentence-based splitting to a more rudimentary, fixed-size character-based splitting to ensure that no single piece of text passed to the next stage is overwhelmingly large, which is a critical consideration for maintaining performance and staying within the context window limitations of many downstream language models. Finally, we return to the original topic. The overlap between chunks is crucial.
    """

    print("--- Testing Hybrid Semantic Chunking ---")
    
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    hybrid_chunks = chunk_text_hybrid(
        sample_text, 
        model=embedding_model, 
        similarity_threshold=0.4,
        sentence_overlap=1
    )
    
    print(f"\nGenerated {len(hybrid_chunks)} hybrid chunks.")
    print("-" * 20)
    
    for i, chunk in enumerate(hybrid_chunks):
        print(f"Chunk {i+1}:\n\"{chunk}\"\n")