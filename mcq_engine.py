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

def generate_mcqs(
    context_text: str,
    api_key: str,
    num_questions: int = 5,
    target_language: str = "Same as document",
    difficulty: str = "Medium",
    focus_topic: str = ""  # NEW PARAMETER
) -> QuizResponse:
    
    client = genai.Client(api_key=api_key)

    # Dynamic instruction based on user choice
    topic_instruction = ""
    if focus_topic.strip():
        topic_instruction = f"CRITICAL: FOCUS EXCLUSIVELY ON THE TOPIC '{focus_topic}'. Ignore unrelated sections of the text."
    else:
        topic_instruction = "Generate questions covering the overall provided text comprehensively."

    prompt = f"""
    You are an expert multilingual academic examiner.
    Analyze the following text and generate {num_questions} high-quality Multiple Choice Questions (MCQs).

    {topic_instruction}

    CRITICAL RULES:
    1. Language constraint: {target_language}.
    2. Difficulty level: {difficulty}.
    3. The 3 distractors (wrong answers) must be plausible and contextually relevant.
    4. Ensure the correct answer is identical to one of the 4 elements in the 'options' list.
    5. Do not hallucinate facts outside the provided text.

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