import os
import time
from datetime import datetime
from extractor import extract_text_from_pdf
from mcq_engine import (
    chat_with_pdf,
    evaluate_descriptive_answer,
    explain_algorithm_or_code,
    generate_descriptive_question,
    generate_flashcards_from_text,
    generate_mcqs,
    summarize_text,
)
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# --- Page Configuration & Modern Theme Styling ---
st.set_page_config(
    page_title="EduAI Suite | Smart Learning Toolkit",
    page_icon="⚡",
    layout="wide",
)

st.markdown(
    """
<style>
    /* Gradient App Bar Header */
    .hero-banner {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 24px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        text-align: center;
    }
    .hero-banner h1 {
        color: #ffffff;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .hero-banner p {
        color: #e0e7ff;
        font-size: 15px;
        margin: 0;
    }
    /* Card Container */
    .content-card {
        background: #ffffff;
        padding: 24px;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-top: 15px;
    }
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8fafc;
    }
</style>
""",
    unsafe_allow_html=True,
)

api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

# --- Session State Initialization ---
states = {
    "pdf_text": "",
    "pdf_name": "",
    "active_interface": "mcq",
    "quiz_data": None,
    "quiz_history": [],
    "user_answers": {},
    "quiz_submitted": False,
    "start_time": None,
    "summary_result": None,
    "summary_flashcards": None,
    "chat_messages": [],
    "exam_question": "",
    "exam_evaluation": None,
}
for key, val in states.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- Top App Header ---
st.markdown(
    """
<div class="hero-banner">
    <h1>⚡ EduAI Academic Intelligence Suite</h1>
    <p>Upload your PDF document once to generate interactive quizzes, summaries, real-time tutoring, code analysis, and essay evaluations.</p>
</div>
""",
    unsafe_allow_html=True,
)

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ Global Settings")
    language_choice = st.selectbox(
        "🌐 Output Language",
        [
            "Same as document",
            "English",
            "Hindi (हिन्दी)",
            "Tamil (தமிழ்)",
            "Telugu (తెలుగు)",
            "Spanish (Español)",
        ],
    )
    st.divider()

    st.subheader("🎯 Quiz Options")
    num_questions = st.slider("Number of MCQs", 3, 15, 5)
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    timer_mins = st.selectbox("Quiz Timer (Minutes)", [5, 10, 15, 30])
    st.divider()

    if not api_key:
        st.error("⚠️ GEMINI_API_KEY not found in Streamlit Secrets.")

# --- Document Upload Bar ---
uploaded_file = st.file_uploader(
    "📂 Upload Course Material / Notes (PDF)", type=["pdf"]
)

if uploaded_file and (uploaded_file.name != st.session_state.pdf_name):
    with st.spinner("Extracting content from PDF..."):
        text = extract_text_from_pdf(uploaded_file)
        if text.strip():
            st.session_state.pdf_text = text
            st.session_state.pdf_name = uploaded_file.name
            st.success(
                f"✅ Successfully loaded: **{uploaded_file.name}** ({len(text)} characters extracted)"
            )
        else:
            st.error("Could not extract readable text from this PDF.")

st.markdown("---")

# --- All 5 Interactive Interface Buttons (Side by Side) ---
st.write("### 🧭 Choose Learning Tool")
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    if st.button("📝 MCQ Generator", use_container_width=True):
        st.session_state.active_interface = "mcq"
with c2:
    if st.button("📄 Summarizer", use_container_width=True):
        st.session_state.active_interface = "summary"
with c3:
    if st.button("💬 Chat Doubt Solver", use_container_width=True):
        st.session_state.active_interface = "chat"
with c4:
    if st.button("💻 Code Explainer", use_container_width=True):
        st.session_state.active_interface = "code"
with c5:
    if st.button("✍️ Exam Evaluator", use_container_width=True):
        st.session_state.active_interface = "exam"

st.markdown("---")

# =========================================================
# INTERFACE 1: CHAT WITH PDF DOUBT SOLVER
# =========================================================
if st.session_state.active_interface == "chat":
    st.subheader("💬 Chat with Document & Doubt Solver")
    if not st.session_state.pdf_text:
        st.info("👆 Please upload a PDF above to start resolving your doubts.")
    else:
        # Display existing message history
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Ask any doubt about the uploaded material:")
        if user_input:
            st.session_state.chat_messages.append(
                {"role": "user", "content": user_input}
            )
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing document to resolve doubt..."):
                    reply = chat_with_pdf(
                        context_text=st.session_state.pdf_text,
                        user_query=user_input,
                        chat_history=st.session_state.chat_messages,
                        api_key=api_key,
                        target_language=language_choice,
                    )
                    st.markdown(reply)
                    st.session_state.chat_messages.append(
                        {"role": "assistant", "content": reply}
                    )

# =========================================================
# INTERFACE 2: CODE & ALGORITHM EXPLAINER
# =========================================================
elif st.session_state.active_interface == "code":
    st.subheader("💻 Code & Algorithm Explainer")
    st.write(
        "Paste any code snippet, sorting algorithm, or recurrence function to break down complexity and mechanics."
    )

    code_input = st.text_area(
        "Input Code / Algorithm:",
        height=200,
        placeholder="e.g., def heapify(arr, n, i): ...",
    )

    if st.button("🔍 Explain Algorithm & Complexity", type="primary"):
        if not code_input.strip():
            st.warning("Please paste a code snippet first.")
        else:
            with st.spinner("Performing algorithmic breakdown..."):
                explanation = explain_algorithm_or_code(
                    code_text=code_input,
                    api_key=api_key,
                    target_language=language_choice,
                )
                st.markdown(explanation)

# =========================================================
# INTERFACE 3: DESCRIPTIVE EXAM EVALUATOR
# =========================================================
elif st.session_state.active_interface == "exam":
    st.subheader("✍️ Descriptive Exam Evaluator")
    if not st.session_state.pdf_text:
        st.info("👆 Please upload a PDF above to generate descriptive exams.")
    else:
        col_gen, _ = st.columns([2, 3])
        with col_gen:
            if st.button("🎲 Generate University Exam Question"):
                with st.spinner("Synthesizing challenging question..."):
                    st.session_state.exam_question = (
                        generate_descriptive_question(
                            context_text=st.session_state.pdf_text,
                            api_key=api_key,
                            target_language=language_choice,
                        )
                    )
                    st.session_state.exam_evaluation = None
                    st.rerun()

        if st.session_state.exam_question:
            st.info(f"### Question:\n{st.session_state.exam_question}")

            answer_input = st.text_area(
                "Type your descriptive answer / proof:",
                height=220,
                placeholder="Write out your complete answer, derivations, or algorithmic steps here...",
            )

            if st.button("📤 Submit for Grading", type="primary"):
                if not answer_input.strip():
                    st.warning("Please write an answer before submitting.")
                else:
                    with st.spinner("Evaluating answer and computing rubric..."):
                        evaluation = evaluate_descriptive_answer(
                            question=st.session_state.exam_question,
                            student_answer=answer_input,
                            context_text=st.session_state.pdf_text,
                            api_key=api_key,
                            target_language=language_choice,
                        )
                        st.session_state.exam_evaluation = evaluation
                        st.rerun()

        if st.session_state.exam_evaluation:
            st.markdown("### 📊 Assessment & Score Report")
            st.markdown(st.session_state.exam_evaluation)

# =========================================================
# INTERFACE 4: TEXT SUMMARIZER & FLASHCARDS
# =========================================================
elif st.session_state.active_interface == "summary":
    st.subheader("📄 Multilingual Document Summary")
    if not st.session_state.pdf_text:
        st.info("👆 Please upload a PDF above to generate a summary.")
    else:
        if st.button("Generate Comprehensive Summary", type="primary"):
            with st.spinner("Extracting insights and generating summary..."):
                st.session_state.summary_result = summarize_text(
                    st.session_state.pdf_text, api_key, language_choice
                )
                st.session_state.summary_flashcards = None
                st.rerun()

        if st.session_state.summary_result:
            st.markdown(st.session_state.summary_result)
            st.divider()
            st.subheader("🗂️ Flashcard Conversion")
            if st.button("Convert Summary to Flashcards"):
                with st.spinner("Extracting flashcards..."):
                    fc_data = generate_flashcards_from_text(
                        st.session_state.summary_result,
                        api_key,
                        language_choice,
                    )
                    st.session_state.summary_flashcards = fc_data.flashcards
                    st.rerun()

            if st.session_state.summary_flashcards:
                df_fc = pd.DataFrame(
                    [
                        {"Front": fc.front, "Back": fc.back}
                        for fc in st.session_state.summary_flashcards
                    ]
                )
                st.dataframe(df_fc, use_container_width=True)
                st.download_button(
                    label="📥 Download Anki/Quizlet CSV",
                    data=df_fc.to_csv(index=False).encode("utf-8"),
                    file_name="flashcards.csv",
                    mime="text/csv",
                )

# =========================================================
# INTERFACE 5: MCQ QUIZ ENGINE & TIMER
# =========================================================
elif st.session_state.active_interface == "mcq":
    st.subheader("📝 Interactive MCQ Generator")
    if not st.session_state.pdf_text:
        st.info("👆 Please upload a PDF above to generate interactive MCQs.")
    else:
        focus_topic = st.text_input(
            "🔍 Focus on a micro-topic (optional):",
            placeholder="e.g., QuickSort Partitioning, Recurrence Relations",
        )

        if st.button("🚀 Start New Quiz", type="primary"):
            with st.spinner("Generating targeted MCQs..."):
                st.session_state.quiz_data = generate_mcqs(
                    st.session_state.pdf_text,
                    api_key,
                    num_questions,
                    language_choice,
                    difficulty,
                    focus_topic,
                )
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.start_time = time.time()
                st.rerun()

        if st.session_state.quiz_data:
            quiz = st.session_state.quiz_data.quiz

            if not st.session_state.quiz_submitted:
                elapsed = int(time.time() - st.session_state.start_time)
                rem = max(0, (timer_mins * 60) - elapsed)
                timer_html = f"""
                <div style="font-size: 20px; font-weight: bold; color: #e11d48; text-align: right; font-family: sans-serif;">
                    ⏳ Time Left: <span id="time">{rem // 60}:{rem % 60:02d}</span>
                </div>
                <script>
                    var t = {rem};
                    var tmr = setInterval(function() {{
                        t--;
                        var m = Math.floor(t / 60);
                        var s = t % 60;
                        document.getElementById("time").innerHTML = m + ":" + (s < 10 ? "0" : "") + s;
                        if (t <= 0) clearInterval(tmr);
                    }}, 1000);
                </script>
                """
                components.html(timer_html, height=45)

            st.markdown("---")
            for i, item in enumerate(quiz, 1):
                st.markdown(f"**Q{i}. {item.question}**")
                st.session_state.user_answers[i] = st.radio(
                    label=f"Options Q{i}",
                    options=item.options,
                    key=f"q_{i}",
                    index=None
                    if not st.session_state.quiz_submitted
                    else (
                        item.options.index(st.session_state.user_answers.get(i))
                        if st.session_state.user_answers.get(i) in item.options
                        else None
                    ),
                    disabled=st.session_state.quiz_submitted,
                    label_visibility="collapsed",
                )
                st.write("")

            if not st.session_state.quiz_submitted:
                if st.button("Submit Quiz", type="primary"):
                    score = sum(
                        1
                        for i, item in enumerate(quiz, 1)
                        if st.session_state.user_answers.get(i)
                        == item.correct_answer
                    )
                    st.session_state.quiz_history.append(
                        {
                            "Date & Time": datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "PDF": st.session_state.pdf_name,
                            "Score": f"{score}/{len(quiz)}",
                        }
                    )
                    st.session_state.final_score = score
                    st.session_state.quiz_submitted = True
                    st.rerun()

            if st.session_state.quiz_submitted:
                st.success(
                    f"### Quiz Complete! Your Score: {st.session_state.final_score} / {len(quiz)}"
                )

                if st.checkbox("Show Explanations & Review"):
                    for i, item in enumerate(quiz, 1):
                        user_ans = st.session_state.user_answers.get(i)
                        if user_ans == item.correct_answer:
                            st.info(
                                f"**Q{i}.** {item.question}\n\n✅ **Your Answer:** {user_ans}\n\n*Explanation:* {item.explanation}"
                            )
                        else:
                            st.error(
                                f"**Q{i}.** {item.question}\n\n❌ **Your Answer:** {user_ans}\n\n🎯 **Correct Answer:** {item.correct_answer}\n\n*Explanation:* {item.explanation}"
                            )

                st.divider()
                st.subheader("🗂️ Export Quiz Flashcards")
                df_mcq_fc = pd.DataFrame(
                    [
                        {
                            "Front": f"{q.question}\n\n" + "\n".join(q.options),
                            "Back": f"{q.correct_answer}\n\nExplanation: {q.explanation}",
                        }
                        for q in quiz
                    ]
                )
                st.download_button(
                    label="📥 Download MCQ Flashcards (CSV)",
                    data=df_mcq_fc.to_csv(index=False).encode("utf-8"),
                    file_name="mcq_flashcards.csv",
                    mime="text/csv",
                )