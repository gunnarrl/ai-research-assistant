# gemini_service.py

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API with your key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file.")

genai.configure(api_key=api_key)

# Initialize the Generative Model
# Using gemini-1.5-flash for speed and cost-effectiveness
model = genai.GenerativeModel('gemini-1.5-flash')

async def generate_summary(text_to_summarize: str) -> str:
    """
    Uses the Gemini API to generate a summary for the given text.

    Args:
        text_to_summarize: The text extracted from the PDF.

    Returns:
        A string containing the AI-generated summary.
    """
    try:
        # Create a specific prompt for the summarization task
        prompt = f"""
        Please provide a concise, academic-style summary of the following text.
        Focus on the key findings, methodology, and conclusions.

        ---
        TEXT:
        {text_to_summarize}
        ---

        SUMMARY:
        """

        # Use the async version of the API call to not block the server
        response = await model.generate_content_async(prompt)

        # Return the generated text
        return response.text

    except Exception as e:
        # Handle potential API errors
        print(f"An error occurred with the Gemini API: {e}")
        return "Error: Could not generate a summary."