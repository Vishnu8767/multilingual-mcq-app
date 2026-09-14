from typing import List
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class MCQItem(BaseModel):
    question: str = Field(description="The question prompt.")
    options: List[str] = Field(description="List of 4 options (A, B, C, D).", min_items=4, max_items=4)
    correct_answer: str = Field(description="The exact text of the correct option matching one in options.")
    explanation: str = Field(description="Brief explanation why this option is correct.")

class QuizResponse(BaseModel):
    detected_language: str = Field(description="Language detected from the document.")
    quiz: List[MCQItem]

class FlashcardItem(BaseModel):
    front: str = Field(description="The core concept, theorem, code snippet, or question.")
    back: str = Field(description="The definition, complexity analysis, proof, or answer.")

class FlashcardResponse(BaseModel):
    flashcards: List[FlashcardItem]

def generate_mcqs(
    context_text: str, api_key: str, num_questions: int = 5,
    target_language: str = "Same as document", difficulty: str = "Medium", focus_topic: str = ""
) -> QuizResponse:
    
    client = genai.Client(api_key=api_key)
    topic_instruction = f"CRITICAL: FOCUS EXCLUSIVELY ON THE TOPIC '{focus_topic}'." if focus_topic.strip() else "Generate questions covering the text."

    prompt = f"""
    You are an expert multilingual academic examiner.
    Analyze the text and generate {num_questions} Multiple Choice Questions (MCQs).

    {topic_instruction}

    CRITICAL RULES:
    1. Language: {target_language}. Difficulty: {difficulty}.
    2. Format all programming code snippets using Markdown code blocks.
    3. Format all mathematical formulas, recurrence relations, and computational time complexities (e.g., O(n log n)) strictly using LaTeX notation.
    4. Ensure the correct answer is exactly one of the 4 options.

    Source Text:
    \"\"\"{context_text[:12000]}\"\"\"
    """
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QuizResponse,
            temperature=0.3,
        ),
    )
    return QuizResponse.model_validate_json(response.text)

def summarize_text(context_text: str, api_key: str, target_language: str = "Same as document") -> str:
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Provide a comprehensive, highly accurate summary of the following text.
    
    CRITICAL RULES:
    1. Output Language: {target_language}.
    2. Format all programming code snippets using standard Markdown code blocks.
    3. Format all mathematical formulas, proofs, and time complexities using LaTeX notation.
    4. Use clear headings and bullet points.

    Source Text:
    \"\"\"{context_text[:15000]}\"\"\"
    """
    response = client.models.generate_content(
        model="gemini-3.6-flash", contents=prompt,
        config=types.GenerateContentConfig(temperature=0.3)
    )
    return response.text

def generate_flashcards_from_text(context_text: str, api_key: str, target_language: str) -> FlashcardResponse:
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Extract the most critical definitions, code snippets, algorithms, and formulas from the text and create high-yield flashcards.
    
    CRITICAL RULES:
    1. Language: {target_language}.
    2. Format all mathematical notation in LaTeX and code in Markdown.
    3. The 'front' should be a clear prompt/concept, and the 'back' should be the answer/definition.

    Source Text:
    \"\"\"{context_text[:12000]}\"\"\"
    """
    response = client.models.generate_content(
        model="gemini-3.6-flash", contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FlashcardResponse,
            temperature=0.3,
        ),
    )
    return FlashcardResponse.model_validate_json(response.text)