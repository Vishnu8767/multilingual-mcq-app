import os
import time
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from extractor import extract_text
from mcq_engine import generate_mcqs, summarize_text

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
    st.error("⚠️ API Key is missing! Please configure GEMINI_API_KEY in Streamlit Secrets.")

tab_quiz, tab_history = st.tabs(["📝 Document Processing", "📊 Quiz History"])

# --- 3. MAIN APPLICATION LOGIC ---
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

    # Check if we have either a file OR typed text ready
    if (uploaded_file or pasted_text.strip()) and api_key:
        col1, col2 = st.columns(2)
        
        # Helper function to get text based on user choice
        def get_source_text():
            if input_method == "Upload Document (PDF, Word, PPT)" and uploaded_file:
                return extract_text(uploaded_file)
            return pasted_text

        # Logic: Summarization
        if col2.button("📄 Summarize Text", use_container_width=True):
            with st.spinner("Generating summary..."):
                text = get_source_text()
                if text.strip():
                    st.session_state.summary_result = summarize_text(text, api_key, language_choice)
                    st.session_state.update({"quiz_data": None})
                    st.rerun()
                else:
                    st.error("No readable text found. Please check your file or input.")

        # Logic: Quiz Generation
        if col1.button("📝 Generate Quiz", type="primary", use_container_width=True):
            with st.spinner("Generating quiz..."):
                text = get_source_text()
                if text.strip():
                    # Set a display name for the history tab
                    display_name = uploaded_file.name if input_method == "Upload Document (PDF, Word, PPT)" else "Direct Text Input"
                    
                    st.session_state.quiz_data = generate_mcqs(text, api_key, num_questions, language_choice, difficulty, focus_topic)
                    st.session_state.update({
                        "summary_result": None, "user_answers": {}, 
                        "quiz_submitted": False, "start_time": time.time(), 
                        "file_name": display_name
                    })
                    st.rerun()
                else:
                    st.error("No readable text found. Please check your file or input.")

    # --- 4. USER INTERFACE RENDERING ---
    if st.session_state.summary_result:
        st.info("### 📄 Document Summary")
        st.markdown(st.session_state.summary_result)

    elif st.session_state.quiz_data:
        quiz = st.session_state.quiz_data.quiz
        
        # Timer Display
        if not st.session_state.quiz_submitted:
            rem = max(0, (timer_mins * 60) - int(time.time() - st.session_state.start_time))
            components.html(f'<div style="font-size: 24px; font-weight: bold; color: #ff4b4b; text-align: right; font-family: sans-serif;">⏳ Time: <span id="time">{rem // 60}:{rem % 60:02d}</span></div><script>var t={rem};setInterval(()=>{{if(t>0)t--;document.getElementById("time").innerHTML=Math.floor(t/60)+":"+(t%60<10?"0":"")+t%60;}},1000);</script>', height=50)

        # Render Questions
        for i, item in enumerate(quiz, 1):
            st.markdown(f"**Q{i}. {item.question}**")
            current_ans = st.session_state.user_answers.get(i)
            idx = item.options.index(current_ans) if current_ans in item.options else None
            
            st.session_state.user_answers[i] = st.radio(
                f"Options Q{i}", item.options, key=f"q_{i}", index=idx,
                disabled=st.session_state.quiz_submitted, label_visibility="collapsed"
            )
            st.write("")

        # Submit & Review Logic
        if not st.session_state.quiz_submitted and st.button("Submit Quiz", type="primary"):
            score = sum(1 for i, item in enumerate(quiz, 1) if st.session_state.user_answers.get(i) == item.correct_answer)
            st.session_state.quiz_history.append({"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "File Name": st.session_state.file_name, "Score": f"{score}/{len(quiz)}"})
            st.session_state.update({"final_score": score, "quiz_submitted": True})
            st.rerun()

        if st.session_state.quiz_submitted:
            st.success(f"### Score: {st.session_state.final_score} / {len(quiz)}")
            
            if st.button("Start New Quiz"):
                st.session_state.update({"quiz_data": None, "quiz_submitted": False})
                st.rerun()

# --- 5. HISTORY TAB ---
with tab_history:
    st.header("📊 Quiz History")
    if st.session_state.quiz_history:
        st.dataframe(pd.DataFrame(st.session_state.quiz_history), use_container_width=True)
    else:
        st.info("No quizzes taken yet.")