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
        Based on the original topic below, please select the 8 to 10 most relevant papers from the provided list.

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
    
async def _get_review_themes(topic: str, synthesis_data: List[Dict]) -> Dict:
    """
    Analyzes all key findings and groups them into 2-4 common themes.
    This serves as the outline for the literature review.
    """
    try:
        # Format the findings for the prompt, mapping them to their source number
        findings_context = ""
        for i, data in enumerate(synthesis_data):
            ref_num = i + 1
            findings = data.get('structured_data', {}).get('key_findings', [])
            if findings:
                findings_str = "\n".join(f"- {f}" for f in findings)
                findings_context += f"Source [{ref_num}]:\n{findings_str}\n\n"

        prompt = f"""
        You are a research analyst tasked with creating an outline for a literature review on the topic of "{topic}".
        Based on the key findings from the sources provided below, identify 2-4 main themes that connect these findings.

        INSTRUCTIONS:
        - Your output must be ONLY a valid JSON object.
        - The JSON object should have a single key: "themes".
        - The value of "themes" should be a list of objects, where each object has two keys: "theme_name" and "sources".
        - "theme_name" should be a concise title for the theme.
        - "sources" should be a list of the integer source numbers relevant to that theme.

        EXAMPLE OUTPUT:
        {{
          "themes": [
            {{
              "theme_name": "AI Code Detection and Stylometry",
              "sources": [1, 3, 5]
            }},
            {{
              "theme_name": "Developer Perceptions and Challenges with AI Tools",
              "sources": [2, 4]
            }}
          ]
        }}

        --- KEY FINDINGS ---
        {findings_context}
        ---

        JSON OUTPUT:
        """
        response = await model.generate_content_async(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(json_text)

    except Exception as e:
        print(f"An error occurred during thematic analysis: {e}")
        return {"themes": []} # Return a safe default

# --- STEP 2: NEW FUNCTION FOR SYNTHESIZING PARAGRAPHS ---
async def _synthesize_theme_paragraph(topic: str, theme_name: str, sources_for_theme: List[Dict]) -> str:
    """
    Writes a detailed paragraph for a single theme, based on a focused set of findings.
    """
    try:
        # Format the findings just for this theme
        findings_context = ""
        for data in sources_for_theme:
            ref_num = data['ref_num']
            findings = data.get('structured_data', {}).get('key_findings', [])
            if findings:
                findings_str = "\n".join(f"- {f}" for f in findings)
                findings_context += f"Source [{ref_num}]:\n{findings_str}\n\n"

        prompt = f"""
        You are writing a section of a literature review on the topic of "{topic}".
        Your current section is titled: "{theme_name}".

        Based ONLY on the findings from the sources provided below, write a cohesive, detailed paragraph.
        Synthesize, compare, and contrast the findings from the different sources.
        When you use information from a source, you MUST cite it using its corresponding number (e.g., [1], [5], etc.).

        --- RELEVANT FINDINGS ---
        {findings_context}
        ---

        PARAGRAPH:
        """
        response = await model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"An error occurred during paragraph synthesis for theme '{theme_name}': {e}")
        return "" # Return empty string on failure


# --- STEP 3: REFACTOR THE MAIN SYNTHESIS FUNCTION ---
async def synthesize_literature_review(topic: str, synthesis_data: List[Dict]) -> str:
    """
    Orchestrates a multi-step process to create a high-quality literature review.
    """
    try:
        # 1. Generate the outline
        print(f"Synthesizing review for '{topic}': Step 1 - Thematic Analysis...")
        themed_outline = await _get_review_themes(topic, synthesis_data)
        if not themed_outline or not themed_outline.get('themes'):
            raise Exception("Failed to generate a thematic outline.")

        # 2. Generate a paragraph for each theme concurrently
        print(f"Synthesizing review for '{topic}': Step 2 - Writing Theme Paragraphs...")
        paragraph_tasks = []
        for theme in themed_outline['themes']:
            theme_name = theme['theme_name']
            source_nums = theme['sources']
            
            # Gather the full data for the sources under this theme
            sources_for_theme = []
            for num in source_nums:
                # Add the ref_num to the data for easy access in the prompt
                synthesis_data[num-1]['ref_num'] = num 
                sources_for_theme.append(synthesis_data[num-1])

            task = _synthesize_theme_paragraph(topic, theme_name, sources_for_theme)
            paragraph_tasks.append(task)
        
        # Run all paragraph generation tasks in parallel
        theme_paragraphs = await asyncio.gather(*paragraph_tasks)

        # 3. Assemble the final review
        print(f"Synthesizing review for '{topic}': Step 3 - Assembling Final Document...")
        final_review_text = f"# Literature Review: {topic}\n\n"
        
        for i, theme in enumerate(themed_outline['themes']):
            final_review_text += f"## {theme['theme_name']}\n\n"
            final_review_text += theme_paragraphs[i] + "\n\n"
            
        # Add the references section
        final_review_text += "## References\n\n"
        reference_list = []
        for i, data in enumerate(synthesis_data):
            citation = data.get('source_citation', {})
            authors = ", ".join(citation.get('authors', []))
            year = citation.get('year', 'N/A')
            title = citation.get('title', data.get('filename'))
            reference_list.append(f"[{i+1}] {authors} ({year}). *{title}*.")
        
        final_review_text += "\n".join(reference_list)

        return final_review_text

    except Exception as e:
        print(f"An error occurred during the multi-step literature review synthesis: {e}")
        return "Failed to generate the literature review due to an internal error."

def parse_references_from_text_sync(context: str) -> List[Dict]:
    """
    Synchronous version of the citation parsing function.
    """
    try:
        # The prompt is identical to the async version
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
        
        # Use the synchronous generate_content method
        response = model.generate_content(prompt)
        
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(json_text)

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Gemini API response during sync citation parsing: {e}")
        return [{"error": "Failed to parse JSON from AI response."}]
    except Exception as e:
        print(f"An error occurred with the Gemini API during sync citation parsing: {e}")
        return [{"error": "Could not parse citations."}]

def generate_bibtex_from_text_sync(context: str) -> str:
    """
    Uses the Gemini API to generate a BibTeX citation from the full text of a paper.
    """
    try:
        # A highly specific prompt to get just the BibTeX entry
        prompt = f"""
        Act as a professional librarian. Your task is to generate a single, complete BibTeX citation for the research paper provided below.
        
        INSTRUCTIONS:
        - Analyze the text to identify the title, authors, and publication year.
        - Create a BibTeX key based on the first author's last name and the year.
        - The response should be ONLY the BibTeX entry, formatted correctly. Do not include any extra text, explanations, or markdown formatting like ```bibtex.

        EXAMPLE OUTPUT:
        @article{{Larsen2025,
          title={{Exploring Large Language Models for Analyzing and Improving Method Names in Scientific Code}},
          author={{Larsen, Gunnar and Wong, Carol and Peruma, Anthony}},
          year={{2025}}
        }}

        --- PAPER TEXT ---
        {context[:15000]} 
        ---

        BIBTEX ENTRY:
        """
        # We use a slice of the text to avoid making the prompt too long
        
        response = model.generate_content(prompt)
        
        # Clean up the response to ensure it's just the BibTeX
        bibtex_entry = response.text.strip()
        return bibtex_entry

    except Exception as e:
        print(f"An error occurred during BibTeX generation: {e}")
        return "@misc{error, title = {Failed to generate BibTeX citation}}"
 