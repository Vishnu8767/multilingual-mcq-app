from typing import List
from google import genai
from pydantic import BaseModel, Field

# --- 1. Define Pydantic Models ---
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


# --- 2. Initialize Client Globally ---
# Replace "YOUR_API_KEY" or rely on the GEMINI_API_KEY environment variable.
client = genai.Client(api_key="YOUR_API_KEY") 
MODEL_ID = "gemini-1.5-flash"


# --- 3. Simplified Functions ---
def generate_mcqs(context_text: str, num_questions: int = 5, target_language: str = "Same as document", difficulty: str = "Medium", focus_topic: str = "") -> QuizResponse:
    topic_instruction = f"CRITICAL: FOCUS EXCLUSIVELY ON THE TOPIC '{focus_topic}'." if focus_topic.strip() else "Generate questions covering the text."
    
    prompt = f"""
    Generate {num_questions} Multiple Choice Questions (MCQs). {topic_instruction}
    Language: {target_language}. Difficulty: {difficulty}.
    Format code using Markdown. Format math/time complexities using LaTeX.
    Ensure the correct answer matches exactly one of the 4 options.
    
    Source Text: \"\"\"{context_text[:12000]}\"\"\"
    """
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": QuizResponse,
            "temperature": 0.3
        }
    )
    return response.parsed

def summarize_text(context_text: str, target_language: str = "Same as document") -> str:
    prompt = f"""
    Provide a comprehensive summary of the following text in {target_language}.
    Format code using Markdown. Format math/proofs using LaTeX. Use clear headings and bullets.
    
    Source Text: \"\"\"{context_text[:15000]}\"\"\"
    """
    response = client.models.generate_content(
        model=MODEL_ID, 
        contents=prompt,
        config={"temperature": 0.3}
    )
    return response.text

def generate_flashcards(context_text: str, target_language: str = "Same as document") -> FlashcardResponse:
    prompt = f"""
    Extract critical definitions, code snippets, and formulas to create high-yield flashcards.
    Language: {target_language}. Format math in LaTeX and code in Markdown.
    
    Source Text: \"\"\"{context_text[:12000]}\"\"\"
    """
    response = client.models.generate_content(
        model=MODEL_ID, 
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": FlashcardResponse,
            "temperature": 0.3
        }
    )
    return response.parsed