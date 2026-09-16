import os
import time
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from google.genai.errors import ServerError

from extractor import extract_text
from mcq_engine import generate_mcqs, summarize_text

# --- Universal Data Parser ---
def parse_quiz_data(raw_data):
    """Safely extracts a list of question dictionaries regardless of the AI's output format."""
    if raw_data is None:
        return []

    # 1. Normalize Pydantic objects to standard dictionaries
    if hasattr(raw_data, "model_dump"):
        raw_data = raw_data.model_dump()
    elif hasattr(raw_data, "dict"):
        raw_data = raw_data.dict()

    # 2. Unpack Tuples (Prevents the "tuple indices must be integers" error!)
    if isinstance(raw_data, tuple):
        for item in raw_data:
            if isinstance(item, list):
                raw_data = item
                break

    # 3. Extract lists buried inside dictionaries
    if isinstance(raw_data, dict):
        for key in ["mcqs", "questions", "quiz"]:
            if key in raw_data and isinstance(raw_data[key], list):
                raw_data = raw_data[key]
                break
        else:
            # Fallback: grab the first list we find
            for val in raw_data.values():
                if isinstance(val, list):
                    raw_data = val
                    break

    # 4. Clean up individual question items
    cleaned_list = []
    if isinstance(raw_data, list):
        for item in raw_data:
            if hasattr(item, "model_dump"):
                item = item.model_dump()
            elif hasattr(item, "dict"):
                item = item.dict()
            if isinstance(item, dict):
                cleaned_list.append(item)

    return cleaned_list


# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(page_title="Advanced AI Toolkit", page_icon="🎓", layout="wide")
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

def initialize_session_state():
    """Sets up all default variables neatly in one place."""
    defaults = {
        "quiz_data": None, "summary_result": None,
        "quiz_history": [], "user_answers": {}, "quiz_submitted": False,
        "start_time": None, "file_name": ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()


# --- 2. SIDEBAR & FILE UPLOAD ---
with st.sidebar:
    st.header("⚙️ Configuration")
    language_choice = st.selectbox("Output Language", ["Same as document", "English", "Hindi (हिन्दी)", "Tamil (தமிழ்)"])
    st.divider()
    num_questions = st.slider("Number of Questions", 3, 15, 5)
    difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"])
    timer_mins = st.selectbox("Set Timer (Minutes)", [5, 10, 15, 30])

st.title("🎓 Advanced AI Quiz & Summarization Toolkit")

if not api_key:
    st.error("⚠️ API Key is missing! Please configure GEMINI_API_KEY securely.")

tab_quiz, tab_history = st.tabs(["📝 Document Processing", "📊 Quiz History"])

with tab_quiz:
    # --- Input Method Toggle ---
    input_method = st.radio("Choose Input Method:", ["Upload Document (PDF, Word, PPT)", "Type / Paste Text Directly"], horizontal=True)
    
    uploaded_file = None
    pasted_text = ""
    
    if input_method == "Upload Document (PDF, Word, PPT)":
        uploaded_file = st.file_uploader("Upload Course Material", type=["pdf", "docx", "pptx"])
    else:
        pasted_text = st.text_area("Type or paste your notes/text here:", height=200, placeholder="Paste your study material here...")

    focus_topic = st.text_input("🔍 Focus on a specific micro-topic? (Optional)") if st.checkbox("Focus Topic") else ""

    # Helper function to get text based on user choice
    def get_source_text():
        if input_method == "Upload Document (PDF, Word, PPT)" and uploaded_file:
            return extract_text(uploaded_file)
        return pasted_text

    # Check if we have either a file OR typed text ready
    if (uploaded_file or pasted_text.strip()) and api_key:
        col1, col2 = st.columns(2)
        
        # Logic: Generate Quiz
        if col1.button("📝 Generate Quiz", use_container_width=True):
            with st.spinner("Generating quiz..."):
                text = get_source_text()
                if text.strip():
                    try:
                        st.session_state.quiz_data = generate_mcqs(text, api_key, num_questions, language_choice, difficulty, focus_topic)
                        st.session_state.update({"summary_result": None, "user_answers": {}, "quiz_submitted": False})
                        st.rerun()
                    except ServerError as e:
                        if "503" in str(e):
                            st.warning("Google's AI servers are currently very busy. Please wait a moment and try again!")
                        else:
                            st.error(f"A server error occurred: {e}")
                else:
                    st.error("No readable text found. Please check your file.")

        # Logic: Summarization
        if col2.button("📄 Summarize Text", use_container_width=True):
            with st.spinner("Generating summary..."):
                text = get_source_text()
                if text.strip():
                    try:
                        st.session_state.summary_result = summarize_text(text, api_key, language_choice)
                        st.session_state.update({"quiz_data": None})
                        st.rerun()
                    except ServerError as e:
                        if "503" in str(e):
                            st.warning("Google's AI servers are currently very busy. Please wait a moment and try again!")
                        else:
                            st.error(f"A server error occurred: {e}")
                else:
                    st.error("No readable text found. Please check your file or input.")


    # --- DISPLAY LOGIC ---
    if st.session_state.summary_result:
        st.subheader("📄 Document Summary")
        st.markdown(st.session_state.summary_result)
        
    elif st.session_state.quiz_data:
        st.subheader("📝 Lab Assessment Quiz")
        
        # Use our foolproof parser!
        quiz_list = parse_quiz_data(st.session_state.quiz_data)
        
        if not quiz_list:
             st.error("Error: Could not extract question data from the AI's response.")
        else:
            for i, q in enumerate(quiz_list):
                # We use .get() to avoid key errors just in case a field is missing
                question_text = q.get('question', f"Error loading question {i+1}")
                options = q.get('options', [])
                correct_ans = q.get('correct_answer', '')
                explanation = q.get('explanation', '')

                st.markdown(f"**Q{i+1}: {question_text}**")
                
                # Create interactive radio buttons
                st.session_state.user_answers[i] = st.radio(
                    "Select your answer:", 
                    options, 
                    key=f"q_{i}",
                    index=None if not st.session_state.quiz_submitted else (options.index(st.session_state.user_answers.get(i, options[0])) if st.session_state.user_answers.get(i) in options else 0)
                )
                
                # Show explanations if submitted
                if st.session_state.quiz_submitted:
                    if st.session_state.user_answers[i] == correct_ans:
                        st.success(f"Correct! {explanation}")
                    else:
                        st.error(f"Incorrect. The correct answer is: **{correct_ans}**\n\nExplanation: {explanation}")
                st.divider()
                
            if not st.session_state.quiz_submitted:
                if st.button("Submit Quiz"):
                    st.session_state.quiz_submitted = True
                    st.rerun()

with tab_history:
    st.header("📊 Your Past Scores")
    st.info("Score tracking implementation will be added here in future updates.")