import os
import time
from datetime import datetime
import pandas as pd
from extractor import extract_text_from_pdf
from mcq_engine import generate_mcqs, summarize_text, generate_flashcards_from_text
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Advanced AI Toolkit", page_icon="🎓", layout="wide")
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

# Initialize Session States
for key in ["quiz_data", "summary_result", "summary_flashcards", "quiz_history", "user_answers", "quiz_submitted", "start_time"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "quiz_history" and key != "user_answers" else ([] if key == "quiz_history" else {})
if "quiz_submitted" not in st.session_state: st.session_state.quiz_submitted = False

st.title("🎓 Advanced AI Quiz & Summarization Toolkit")

tab_quiz, tab_history = st.tabs(["📝 Document Processing", "📊 Quiz History"])

with tab_quiz:
    with st.sidebar:
        st.header("⚙️ Configuration")
        language_choice = st.selectbox("Output Language", ["Same as document", "English", "Hindi (हिन्दी)", "Tamil (தமிழ்)"])
        st.divider()
        st.subheader("Quiz Parameters")
        num_questions = st.slider("Number of Questions", 3, 15, 5)
        difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"])
        timer_mins = st.selectbox("Set Timer (Minutes)", [5, 10, 15, 30])

    if not api_key:
        st.error("⚠️ API Key is missing! Please configure GEMINI_API_KEY in Streamlit Secrets.")

    uploaded_file = st.file_uploader("Upload Course Material (PDF)", type=["pdf"])
    use_topic = st.checkbox("🔍 Focus on a specific micro-topic? (Optional)")
    focus_topic = st.text_input("Type the specific topic:") if use_topic else ""

    if uploaded_file and api_key:
        col1, col2 = st.columns(2)
        generate_quiz_btn = col1.button("📝 Generate Quiz", type="primary", use_container_width=True)
        summarize_btn = col2.button("📄 Summarize Text", type="secondary", use_container_width=True)

        if summarize_btn:
            with st.spinner("Generating comprehensive summary..."):
                text = extract_text_from_pdf(uploaded_file)
                if text.strip():
                    st.session_state.summary_result = summarize_text(text, api_key, language_choice)
                    st.session_state.summary_flashcards = None
                    st.session_state.quiz_data = None
                    st.rerun()

        if generate_quiz_btn:
            with st.spinner("Generating quiz..."):
                text = extract_text_from_pdf(uploaded_file)
                if text.strip():
                    st.session_state.quiz_data = generate_mcqs(text, api_key, num_questions, language_choice, difficulty, focus_topic)
                    st.session_state.summary_result = None
                    st.session_state.user_answers = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.start_time = time.time()
                    st.session_state.pdf_name = uploaded_file.name
                    st.rerun()

    # --- SUMMARY UI ---
    if st.session_state.summary_result:
        st.info("### 📄 Document Summary")
        st.markdown(st.session_state.summary_result)
        st.divider()
        
        st.subheader("🗂️ Generate Flashcards from Summary")
        if st.button("Create Anki/Quizlet Flashcards"):
            with st.spinner("Extracting key concepts for flashcards..."):
                flashcards_data = generate_flashcards_from_text(st.session_state.summary_result, api_key, language_choice)
                st.session_state.summary_flashcards = flashcards_data.flashcards
                st.rerun()
                
        if st.session_state.summary_flashcards:
            df_fc = pd.DataFrame([{"Front": fc.front, "Back": fc.back} for fc in st.session_state.summary_flashcards])
            st.dataframe(df_fc, use_container_width=True)
            st.download_button(
                label="📥 Download Summary Flashcards (CSV)",
                data=df_fc.to_csv(index=False).encode("utf-8"),
                file_name="summary_flashcards.csv", mime="text/csv"
            )

    # --- QUIZ UI ---
    if st.session_state.quiz_data:
        quiz = st.session_state.quiz_data.quiz
        if not st.session_state.quiz_submitted:
            elapsed = int(time.time() - st.session_state.start_time)
            rem = max(0, (timer_mins * 60) - elapsed)
            components.html(f"""<div style="font-size: 24px; font-weight: bold; color: #ff4b4b; text-align: right; font-family: sans-serif;">⏳ Time Remaining: <span id="time">{rem // 60}:{rem % 60:02d}</span></div>
            <script>var t = {rem}; var tmr = setInterval(function() {{ t--; document.getElementById("time").innerHTML = Math.floor(t / 60) + ":" + (t % 60 < 10 ? "0" : "") + t % 60; if (t <= 0) clearInterval(tmr); }}, 1000);</script>""", height=50)

        st.markdown("---")
        for i, item in enumerate(quiz, 1):
            st.markdown(f"**Q{i}. {item.question}**")
            st.session_state.user_answers[i] = st.radio(
                label=f"Options Q{i}", options=item.options, key=f"q_{i}",
                index=None if not st.session_state.quiz_submitted else (item.options.index(st.session_state.user_answers.get(i)) if st.session_state.user_answers.get(i) in item.options else None),
                disabled=st.session_state.quiz_submitted, label_visibility="collapsed"
            )
            st.write("")

        if not st.session_state.quiz_submitted:
            if st.button("Submit Quiz", type="primary"):
                score = sum(1 for i, item in enumerate(quiz, 1) if st.session_state.user_answers.get(i) == item.correct_answer)
                st.session_state.quiz_history.append({"Date & Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "PDF Name": st.session_state.pdf_name, "Score": f"{score}/{len(quiz)}"})
                st.session_state.final_score = score
                st.session_state.quiz_submitted = True
                st.rerun()

        if st.session_state.quiz_submitted:
            st.success(f"### Quiz Completed! Your Score: {st.session_state.final_score} / {len(quiz)}")
            st.divider()
            st.subheader("🗂️ Export Quiz to Flashcards")
            df_quiz_fc = pd.DataFrame([{"Front": f"{q.question}\n\n" + "\n".join(q.options), "Back": f"{q.correct_answer}\n\nExplanation: {q.explanation}"} for q in quiz])
            st.download_button(
                label="📥 Download MCQ Flashcards (CSV)",
                data=df_quiz_fc.to_csv(index=False).encode("utf-8"),
                file_name="mcq_flashcards.csv", mime="text/csv"
            )
            if st.button("Start New Quiz"):
                st.session_state.quiz_data = None
                st.session_state.quiz_submitted = False
                st.rerun()

with tab_history:
    st.header("📊 User Quiz History")
    if not st.session_state.quiz_history: st.info("No quizzes taken yet.")
    else: st.dataframe(pd.DataFrame(st.session_state.quiz_history), use_container_width=True)