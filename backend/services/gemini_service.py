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

async def get_answer_from_gemini(context: str, question: str) -> str:
    """
    Uses the Gemini API to generate an answer based on provided context and a question.

    Args:
        context: The relevant text chunks retrieved from the database.
        question: The user's question.

    Returns:
        A string containing the AI-generated answer.
    """
    try:
        # Construct a detailed, context-aware prompt
        prompt = f"""
        Based *only* on the following context, please provide a clear and concise answer to the question.
        Do not use any information outside of the provided text. If the answer cannot be found
        in the context, please state that.

        ---
        CONTEXT:
        {context}
        ---

        QUESTION:
        {question}
        ---

        ANSWER:
        """

        # Use the async version of the API call
        response = await model.generate_content_async(prompt)
        return response.text

    except Exception as e:
        # Handle potential API errors
        print(f"An error occurred with the Gemini API: {e}")
        return "Error: Could not generate an answer."