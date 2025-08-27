# backend/utils/text_processing.py

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """
    Splits a long text into smaller, word-aware chunks of a specified size with overlap.

    Args:
        text: The input text to be chunked.
        chunk_size: The desired approximate size of each chunk (in characters).
        chunk_overlap: The number of characters to overlap between consecutive chunks.

    Returns:
        A list of text chunks.
    """
    if not isinstance(text, str) or chunk_overlap >= chunk_size:
        return []

    chunks = []
    start_index = 0
    
    # Iterate through the text
    while start_index < len(text):
        # Determine the potential end of the chunk
        end_index = start_index + chunk_size
        
        # If the potential end is beyond the text length, just take the rest of the text
        if end_index >= len(text):
            chunks.append(text[start_index:])
            break
        
        # Find the last space or newline before the desired end_index to avoid splitting words
        # We search backwards from the potential end_index
        split_index = text.rfind(' ', start_index, end_index)
        if split_index == -1: # No space found, fall back to hard cut
            split_index = end_index
            
        chunks.append(text[start_index:split_index])
        provisional_start = split_index - chunk_overlap
        
        # To ensure the next chunk starts with a complete word, find the first
        # space at or after the provisional start point. We search within the
        # overlap region (from provisional_start to split_index).
        word_boundary = text.find(' ', provisional_start, split_index)
        
        if word_boundary != -1:
            # If a space is found, the next chunk starts right after it.
            start_index = word_boundary + 1
        else:
            # If no space is found in the overlap (e.g., a very long word),
            # fall back to starting where the last chunk ended to avoid errors.
            start_index = split_index

        # Final safety check to prevent getting stuck
        if start_index >= split_index:
            start_index = split_index

    return chunks

# --- Testing Block ---
if __name__ == '__main__':
    sample_text = """This is a long sample text to demonstrate the functionality of the text chunking algorithm. The purpose of chunking is to break down a large document into smaller, more manageable pieces. These pieces, or chunks, can then be processed individually, for example, by converting them into vector embeddings for a Retrieval-Augmented Generation (RAG) system. The overlap between chunks is crucial. It ensures that semantic context is not lost at the boundaries of the chunks. For instance, a sentence that starts at the end of one chunk and finishes at the beginning of the next would be fully preserved in the context of the second chunk due to this overlap. Let's add more text to make sure we get multiple chunks. The total length of this text should be sufficient to generate at least two or three chunks with the default settings of chunk_size=1000 and chunk_overlap=200. We are adding filler content now to extend the length beyond the initial chunk size. This process is repeated until the entire document has been processed and converted into a list of overlapping text strings. The final chunk might be smaller than the specified chunk size, which is perfectly acceptable as it simply contains the remaining text from the document. Testing this function independently is a key part of the development process to ensure its correctness before integrating it into the main application pipeline. This concludes the sample text.
    """

    print(f"Original text length: {len(sample_text)} characters")
    
    text_chunks = chunk_text(sample_text, chunk_size=400, chunk_overlap=80)
    
    print(f"\nGenerated {len(text_chunks)} chunks.")
    print("-" * 20)
    
    # Verify that words are not split between chunks
    for i in range(len(text_chunks) - 1):
        chunk1_end = text_chunks[i][-20:].replace('\n', ' ') # Last 20 chars of chunk i
        chunk2_start = text_chunks[i+1][:20].replace('\n', ' ') # First 20 chars of chunk i+1
        
        print(f"Chunk {i+1} {text_chunks[i]}'")
        # print(f"Chunk {i+2} starts with: '{chunk2_start}...'\n")