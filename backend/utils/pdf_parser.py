#app/utils/pdf_parser.py

import fitz  # PyMuPDF

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts full text content from the in-memory bytes of a PDF file.

    Args:
        file_bytes: The content of the PDF file as bytes.

    Returns:
        A string containing all the extracted text.

    Raises:
        Exception: Propagates exceptions from the PyMuPDF library if the
                   file cannot be processed.
    """
    try:
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        
        # Concatenate text from all pages
        extracted_text = "".join(page.get_text() for page in pdf_document)
        
        pdf_document.close()
        return extracted_text
    except Exception as e:
        print(f"Error during PDF text extraction: {e}")
        # Re-raise the exception to be caught by the API endpoint
        raise

