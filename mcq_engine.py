from typing import List
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# --- Pydantic Data Models ---
class MCQItem(BaseModel):
    question: str = Field(description="The question prompt.")
    options: List[str] = Field(
        description="List of 4 options (A, B, C, D).",
        min_items=4,
        max_items=4,
    )
    correct_answer: str = Field(
        description="The exact text of the correct option matching one in options."
    )
    explanation: str = Field(
        description="Brief explanation why this option is correct."
    )


class QuizResponse(BaseModel):
    detected_language: str = Field(
        description="Language detected from the document."
    )
    quiz: List[MCQItem]


class FlashcardItem(BaseModel):
    front: str = Field(
        description="The core concept, theorem, code snippet, or question."
    )
    back: str = Field(
        description="The definition, complexity analysis, proof, or answer."
    )


class FlashcardResponse(BaseModel):
    flashcards: List[FlashcardItem]


# --- 1. MCQ Generation Engine ---
def generate_mcqs(
    context_text: str,
    api_key: str,
    num_questions: int = 5,
    target_language: str = "Same as document",
    difficulty: str = "Medium",
    focus_topic: str = "",
) -> QuizResponse:
    client = genai.Client(api_key=api_key)
    topic_rule = (
        f"CRITICAL: Focus exclusively on '{focus_topic}'."
        if focus_topic.strip()
        else "Cover the entire document."
    )

    prompt = f"""
    You are an expert academic examiner.
    Generate {num_questions} Multiple Choice Questions (MCQs) from the text below.
    {topic_rule}

    RULES:
    1. Target Language: {target_language}.
    2. Difficulty: {difficulty}.
    3. Format programming code using Markdown code blocks.
    4. Format math formulas and asymptotic complexities using LaTeX (e.g., $O(n \\log n)$).
    5. Options must contain exactly 4 plausible choices.

    Source Text:
    \"\"\"{context_text[:12000]}\"\"\"
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QuizResponse,
            temperature=0.3,
        ),
    )
    return QuizResponse.model_validate_json(response.text)


# --- 2. Text Summarizer Engine ---
def summarize_text(
    context_text: str, api_key: str, target_language: str = "Same as document"
) -> str:
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Provide an elegant, comprehensive summary of the provided text.
    
    RULES:
    1. Output Language: {target_language}.
    2. Format math and recurrence relations with LaTeX.
    3. Format all code snippets in Markdown syntax.
    4. Structure the response cleanly with headings and bullet points.

    Source Text:
    \"\"\"{context_text[:15000]}\"\"\"
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.3),
    )
    return response.text


# --- 3. Flashcards Engine ---
def generate_flashcards_from_text(
    context_text: str, api_key: str, target_language: str
) -> FlashcardResponse:
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Extract high-yield concepts, definitions, and code logic into flashcards.
    Output Language: {target_language}.
    Math in LaTeX, code in Markdown.

    Source Text:
    \"\"\"{context_text[:12000]}\"\"\"
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FlashcardResponse,
            temperature=0.3,
        ),
    )
    return FlashcardResponse.model_validate_json(response.text)


# --- 4. Interface 1: Chat with PDF Engine ---
def chat_with_pdf(
    context_text: str,
    user_query: str,
    chat_history: list,
    api_key: str,
    target_language: str,
) -> str:
    client = genai.Client(api_key=api_key)

    history_str = "\n".join(
        [f"{msg['role'].upper()}: {msg['content']}" for msg in chat_history[-6:]]
    )

    prompt = f"""
    You are an AI Academic Tutor answering questions strictly using the document context provided.
    
    Context:
    \"\"\"{context_text[:15000]}\"\"\"

    Recent Conversation History:
    {history_str}

    Student Query: {user_query}
    Target Language: {target_language}

    Guidelines:
    - Ground your response in the provided document.
    - Format formulas in LaTeX and code in Markdown.
    - Be clear, supportive, and concise.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.4),
    )
    return response.text


# --- 5. Interface 2: Code & Algorithm Explainer Engine ---
def explain_algorithm_or_code(
    code_text: str, api_key: str, target_language: str
) -> str:
    client = genai.Client(api_key=api_key)
    prompt = f"""
    You are an expert Computer Science Professor and Algorithms Specialist.
    Analyze the following code snippet, pseudo-code, or algorithm:

    ```
    {code_text}
    ```

    Structure your explanation in this exact layout:
    1. **Overview & High-Level Purpose**: What the algorithm achieves.
    2. **Line-by-Line / Phase-by-Phase Walkthrough**: Clear, digestible explanation.
    3. **Computational Complexity**:
       - Best Case Time: $O(...)$
       - Worst Case Time: $O(...)$
       - Average Case Time: $O(...)$
       - Space Complexity: $O(...)$
    4. **Recurrence Relation / Mathematical Invariants**: Formal proof/derivation using LaTeX where applicable.
    5. **Edge Cases & Optimizations**: Potential bottlenecks or boundary conditions.

    Target Language: {target_language}.
    """
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2),
    )
    return response.text


# --- 6. Interface 3: Descriptive Exam Evaluator Engine ---
def generate_descriptive_question(
    context_text: str, api_key: str, target_language: str
) -> str:
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Generate one high-yield, academic descriptive exam question (e.g., proof, algorithmic derivation, or conceptual analysis) based on the text.
    Target Language: {target_language}.
    
    Source Text:
    \"\"\"{context_text[:12000]}\"\"\"
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.4),
    )
    return response.text


def evaluate_descriptive_answer(
    question: str,
    student_answer: str,
    context_text: str,
    api_key: str,
    target_language: str,
) -> str:
    client = genai.Client(api_key=api_key)
    prompt = f"""
    You are a university examiner grading a student's open-ended descriptive exam answer.

    Reference Document Material:
    \"\"\"{context_text[:12000]}\"\"\"

    Exam Question:
    {question}

    Student's Submitted Answer:
    \"\"\"{student_answer}\"\"\"

    Evaluate the student's submission and provide feedback in this structure:
    1. **Score**: Assign an objective score out of 10 (e.g., 8/10).
    2. **Key Strengths**: Specific concepts the student explained correctly.
    3. **Missing or Inaccurate Elements**: Crucial points, steps, or edge cases omitted.
    4. **Model Answer & Derivations**: The complete, ideal response with LaTeX math where appropriate.

    Target Language: {target_language}.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2),
    )
    return response.text