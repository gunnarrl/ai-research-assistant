# gemini_service.py

import os
import json
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict

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
    
async def parse_references_from_text(context: str) -> List[Dict]:
    """
    Uses the Gemini API to parse a block of text containing bibliographic references
    into a structured list of dictionaries.

    Args:
        context: The text of the "References" or "Bibliography" section.

    Returns:
        A list of dictionaries, each representing a single citation.
    """
    try:
        prompt = f"""
        Act as a bibliographic assistant. Your task is to parse the provided text, which contains a list of academic references, and convert it into a structured JSON array.

        Each object in the array should represent a single reference and have the following keys: "title", "authors", and "year".

        - "authors" should be a list of author names.
        - If a value for a key cannot be found, use an empty string or an empty list.
        - Ignore reference numbers like "[1]" or "1.".

        Provide the output *only* in a valid JSON format.

        EXAMPLE INPUT:
        REFERENCES
        [1] C. D. Newman, R. S. AlSuhaibani, M. J. Decker, A. Peruma, D. Kaushik, M. W. Mkaouer, and E. Hill, "On the generation, structure, and semantics of grammar patterns in source code identifiers." Journal of Systems and Software, vol. 170, p. 110740, 2020.
        [2] X. Hou, Y. Zhao, Y. Liu, Z. Yang, K. Wang, L. Li, X. Luo, D. Lo, J. Grundy, and H. Wang, "Large language models for software engineering: A systematic literature review," ACM Transactions on Software Engineering and Methodology, vol. 33, p. 1-79, Nov. 2024.

        EXAMPLE OUTPUT:
        [
          {{
            "title": "On the generation, structure, and semantics of grammar patterns in source code identifiers.",
            "authors": ["C. D. Newman", "R. S. AlSuhaibani", "M. J. Decker", "A. Peruma", "D. Kaushik", "M. W. Mkaouer", "E. Hill"],
            "year": "2020"
          }},
          {{
            "title": "Large language models for software engineering: A systematic literature review,",
            "authors": ["X. Hou", "Y. Zhao", "Y. Liu", "Z. Yang", "K. Wang", "L. Li", "X. Luo", "D. Lo", "J. Grundy", "H. Wang"],
            "year": "2024"
          }}
        ]

        ---
        CONTEXT TO PARSE:
        {context}
        ---

        JSON OUTPUT:
        """

        response = await model.generate_content_async(prompt)
        
        # Clean the response to ensure it's valid JSON
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        return json.loads(json_text)

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Gemini API response during citation parsing: {e}")
        print(f"Raw response was: {response.text}")
        return [{"error": "Failed to parse JSON from AI response."}]
    except Exception as e:
        print(f"An error occurred with the Gemini API during citation parsing: {e}")
        return [{"error": "Could not parse citations."}]

async def filter_relevant_papers(topic: str, papers: List[Dict]) -> List[str]:
    """
    Uses the Gemini API to select the most relevant papers from a list based on a topic.

    Args:
        topic: The original research topic.
        papers: A list of paper dictionaries from the arXiv search.

    Returns:
        A list of titles of the papers deemed most relevant by the LLM.
    """
    try:
        # Format the paper details into a string for the prompt
        papers_context = ""
        for paper in papers:
            papers_context += f"Title: {paper['title']}\nSummary: {paper['summary']}\n---\n"

        prompt = f"""
        You are a research assistant helping to build a literature review.
        Based on the original topic below, please select the 3 to 5 most relevant papers from the provided list.

        Your response must be ONLY a JSON array of the exact titles of the papers you select.
        Do not include any other text, explanation, or formatting.

        EXAMPLE OUTPUT:
        [
          "A Large-Scale Study About Quality and Reproducibility of Jupyter Notebooks",
          "On the generation, structure, and semantics of grammar patterns in source code identifiers."
        ]

        ---
        ORIGINAL TOPIC: "{topic}"
        ---
        PAPERS LIST:
        {papers_context}
        ---

        JSON OUTPUT (only the array of titles):
        """

        response = await model.generate_content_async(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        # The result is a list of titles
        return json.loads(json_text)

    except Exception as e:
        print(f"An error occurred while filtering papers with the LLM: {e}")
        # Return an empty list as a safe fallback
        return []
    
async def synthesize_literature_review(topic: str, summaries: List[Dict]) -> str:
    """
    Uses the Gemini API to synthesize a literature review from a list of structured summaries.

    Args:
        topic: The original research topic.
        summaries: A list of structured data dictionaries from processed papers.

    Returns:
        A string containing the synthesized literature review.
    """
    try:
        summaries_context = ""
        for summary in summaries:
            # We added 'source_filename' to the summary dict in the previous step
            filename = summary.get('source_filename', 'Unknown Source')
            summaries_context += f"--- PAPER: {filename} ---\n"
            summaries_context += f"Methodology: {summary.get('methodology', 'N/A')}\n"
            
            findings = summary.get('key_findings', [])
            if findings:
                findings_str = "\n".join(f"- {f}" for f in findings)
                summaries_context += f"Key Findings:\n{findings_str}\n"
            summaries_context += "---\n\n"

        prompt = f"""
        You are a research assistant tasked with writing a literature review.
        Based *only* on the key findings and methodologies from the papers provided below, write a cohesive literature review on the topic of "{topic}".

        Your response should be a well-structured essay. Synthesize and compare the findings from the different papers. 
        When you use information from a specific paper, you MUST cite it by its filename, for example: (e.g., "{summaries[0].get('source_filename', 'example_paper.pdf')}").

        Do not invent any information. Ground your entire review in the provided context.

        ---
        CONTEXT FROM PAPERS:
        {summaries_context}
        ---

        LITERATURE REVIEW:
        """
        
        # Use a non-streaming call to get the full text at once
        response = await model.generate_content_async(prompt)
        
        return response.text

    except Exception as e:
        print(f"An error occurred during literature review synthesis: {e}")
        return "Failed to generate the literature review due to an internal error."
