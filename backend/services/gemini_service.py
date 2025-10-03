# gemini_service.py

import os
import json
import asyncio
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
model = genai.GenerativeModel('gemini-2.5-flash-lite')

async def get_answer_from_gemini(context: str, question: str, is_multi_doc: bool = False) -> str:
    """
    Uses the Gemini API to generate an answer based on provided context and a question.
    Uses a different prompt for multi-document synthesis questions.

    Args:
        context: The relevant text chunks retrieved from the database.
        question: The user's question.
        is_multi_doc: Flag to indicate if the context is from multiple documents.

    Returns:
        A string containing the AI-generated answer.
    """
    try:
        # Choose the prompt based on the context type
        if is_multi_doc:
            prompt = f"""
            You are a research assistant with expertise in synthesizing information from multiple sources.
            Based on the context provided from several documents below, please provide a comprehensive answer to the question.

            Your task is to compare, contrast, and synthesize the information from the different source documents. 
            When you use information from a specific document, cite it by its filename (e.g., "According to 'paper_A.pdf'...", "In contrast, 'paper_B.pdf' states...").

            Do not use any information outside of the provided text. If the answer cannot be reasonably synthesized from the context, please state that.

            ---
            CONTEXT:
            {context}
            ---

            QUESTION:
            {question}
            ---

            ANSWER:
            """
        else:
            # The original, more restrictive prompt for single-document Q&A
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

        response = await model.generate_content_async(prompt, stream=True)

        async for chunk in response:
            yield chunk.text

    except Exception as e:
        print(f"An error occurred with the Gemini API: {e}")
        yield "Error: Could not generate an answer."
    
async def extract_structured_data(context: str) -> dict:
    """
    Uses the Gemini API to extract structured data from a given text.

    Args:
        context: A large block of text from the document.

    Returns:
        A dictionary containing the extracted data.
    """
    try:
        # A more focused prompt designed for JSON output
        prompt = f"""
        Act as a specialized research analyst. Your task is to extract specific pieces of information 
        from the provided text of a research paper.

        Based *only* on the text below, extract the following information:
        1. "methodology": A brief description of the methodology used in the paper.
        2. "dataset": A description of the dataset used, if mentioned. If not mentioned, use an empty string.
        3. "key_findings": A list of key findings or conclusions from the paper.

        Provide the output *only* in a valid JSON format with the following keys: 
        "methodology", "dataset", "key_findings".

        EXAMPLE OUTPUT:
        {{
          "methodology": "The study involved analyzing 691 method names from 384 Jupyter Notebooks using four Large Language Models (LLMs).",
          "dataset": "A dataset of 691 method names from 384 Python-based Jupyter Notebooks collected from public GitHub repositories.",
          "key_findings": [
            "LLMs can provide valuable guidance but require careful human evaluation.",
            "Gemini achieved the highest accuracy in recognizing grammatical patterns.",
            "LLaMA was the most aggressive in proposing alternative names."
          ]
        }}

        ---
        CONTEXT:
        {context}
        ---

        JSON OUTPUT:
        """

        # Use a non-streaming call to get the full response at once
        response = await model.generate_content_async(prompt)

        # Clean the response to ensure it's valid JSON
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()

        # Parse the JSON string into a Python dictionary
        return json.loads(json_text)

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Gemini API response: {e}")
        print(f"Raw response was: {response.text}")
        return {"error": "Failed to parse structured data from AI response."}
    except Exception as e:
        print(f"An error occurred with the Gemini API during data extraction: {e}")
        return {"error": "Could not extract structured data."}
    
def extract_structured_data_sync(context: str) -> dict:
    """
    Synchronous version of the data extraction function.
    """
    try:
        prompt = f"""
        Act as a specialized research analyst. Your task is to extract specific pieces of information 
        from the provided text of a research paper.

        Based *only* on the text below, extract the following information:
        1. "methodology": A brief description of the methodology used in the paper.
        2. "dataset": A description of the dataset used, if mentioned. If not mentioned, use an empty string.
        3. "key_findings": A list of key findings or conclusions from the paper.

        Provide the output *only* in a valid JSON format with the following keys: 
        "methodology", "dataset", "key_findings".

        ---
        CONTEXT:
        {context}
        ---

        JSON OUTPUT:
        """
        # Use the synchronous version of the API call
        response = model.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(json_text)

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Gemini API response: {e}")
        # Use response.text if it exists, otherwise provide a fallback.
        raw_text = getattr(response, 'text', 'No response text available.')
        print(f"Raw response was: {raw_text}")
        return {"error": "Failed to parse structured data from AI response."}
    except Exception as e:
        print(f"An error occurred with the Gemini API during data extraction: {e}")
        return {"error": "Could not extract structured data."}

