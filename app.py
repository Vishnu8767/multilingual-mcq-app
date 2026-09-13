import os
import time
from datetime import datetime
import pandas as pd
from extractor import extract_text_from_pdf
from mcq_engine import generate_mcqs, summarize_text
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Advanced AI Toolkit", page_icon="🎓", layout="wide"
)

api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

# --- Initialize Session States ---
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "summary_result" not in st.session_state:
    st.session_state.summary_result = None
if "quiz_history" not in st.session_state:
    st.session_state.quiz_history = []
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None

st.title("🎓 Advanced AI Quiz & Summarization Toolkit")

tab_quiz, tab_history = st.tabs(["📝 Document Processing", "📊 Quiz History"])

with tab_quiz:
    with st.sidebar:
        st.header("⚙️ Configuration")
        language_choice = st.selectbox(
            "Output Language (Applies to both Quiz & Summary)",
            ["Same as document", "English", "Hindi (हिन्दी)", "Tamil (தமிழ்)", "Telugu (తెలుగు)", "Spanish (Español)"],
        )
        
        st.divider()
        st.subheader("Quiz Parameters")
        num_questions = st.slider("Number of Questions", 3, 15, 5)
        difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"])
        timer_mins = st.selectbox("Set Timer (Minutes)", [5, 10, 15, 30])

    if not api_key:
        st.error(
            "⚠️ API Key is missing! Please configure GEMINI_API_KEY in Streamlit Secrets."
        )

    uploaded_file = st.file_uploader(
        "Upload Course Material (PDF)", type=["pdf"]
    )

    focus_topic = ""
    use_topic = st.checkbox("🔍 Focus on a specific micro-topic? (Optional)")
    if use_topic:
        focus_topic = st.text_input(
            "Type the specific topic (e.g., 'Recurrence Relations', 'Heap Sort'):"
        )

    if uploaded_file and api_key:
        # Create side-by-side buttons
        col1, col2 = st.columns(2)
        with col1:
            generate_quiz_btn = st.button("📝 Generate Quiz", type="primary", use_container_width=True)
        with col2:
            summarize_btn = st.button("📄 Summarize Text", type="secondary", use_container_width=True)

        # Handle Summarization
        if summarize_btn:
            with st.spinner("Extracting text and generating comprehensive summary..."):
                text = extract_text_from_pdf(uploaded_file)
                if not text.strip():
                    st.error("Could not extract readable text.")
                else:
                    try:
                        summary = summarize_text(text, api_key, language_choice)
                        st.session_state.summary_result = summary
                        st.session_state.quiz_data = None # Clear quiz if exists
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        # Handle Quiz Generation
        if generate_quiz_btn:
            with st.spinner("Extracting text and generating quiz..."):
                text = extract_text_from_pdf(uploaded_file)
                if not text.strip():
                    st.error("Could not extract readable text.")
                else:
                    try:
                        quiz_data = generate_mcqs(
                            text, api_key, num_questions, language_choice, difficulty, focus_topic
                        )
                        st.session_state.quiz_data = quiz_data
                        st.session_state.summary_result = None # Clear summary if exists
                        st.session_state.user_answers = {}
                        st.session_state.quiz_submitted = False
                        st.session_state.start_time = time.time()
                        st.session_state.pdf_name = uploaded_file.name
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # Display Summary Result
    if st.session_state.summary_result:
        st.info("### 📄 Document Summary")
        st.markdown(st.session_state.summary_result)
        st.divider()

    # Display Interactive Quiz
    if st.session_state.quiz_data:
        quiz = st.session_state.quiz_data.quiz

        if not st.session_state.quiz_submitted:
            elapsed_seconds = int(time.time() - st.session_state.start_time)
            remaining_seconds = max(0, (timer_mins * 60) - elapsed_seconds)

            timer_html = f"""
            <div style="font-size: 24px; font-weight: bold; color: #ff4b4b; text-align: right; font-family: sans-serif;">
                ⏳ Time Remaining: <span id="time">{remaining_seconds // 60}:{remaining_seconds % 60:02d}</span>
            </div>
            <script>
                var time_left = {remaining_seconds};
                var timer = setInterval(function() {{
                    time_left--;
                    var minutes = Math.floor(time_left / 60);
                    var seconds = time_left % 60;
                    document.getElementById("time").innerHTML = minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
                    if (time_left <= 0) clearInterval(timer);
                }}, 1000);
            </script>
            """
            components.html(timer_html, height=50)

        st.markdown("---")
        for i, item in enumerate(quiz, 1):
            st.markdown(f"**Q{i}. {item.question}**")
            disabled = st.session_state.quiz_submitted

            st.session_state.user_answers[i] = st.radio(
                label=f"Options for Q{i}",
                options=item.options,
                key=f"q_{i}",
                index=(
                    None
                    if not st.session_state.quiz_submitted
                    else (
                        item.options.index(st.session_state.user_answers.get(i))
                        if st.session_state.user_answers.get(i) in item.options
                        else None
                    )
                ),
                disabled=disabled,
                label_visibility="collapsed",
            )
            st.write("")

        if not st.session_state.quiz_submitted:
            st.markdown("---")
            user_name = st.text_input("Enter your name to submit:")

            if st.button("Submit Quiz", type="primary"):
                end_time = time.time()
                time_taken = end_time - st.session_state.start_time
                avg_time_per_q = time_taken / len(quiz)

                score = sum(
                    1
                    for i, item in enumerate(quiz, 1)
                    if st.session_state.user_answers.get(i)
                    == item.correct_answer
                )

                percentage = (score / len(quiz)) * 100
                if percentage == 100:
                    emoji = "🏆"
                elif percentage >= 80:
                    emoji = "🎉"
                elif percentage >= 50:
                    emoji = "👍"
                else:
                    emoji = "📚"

                history_entry = {
                    "Date & Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Name": user_name if user_name else "Anonymous",
                    "PDF Name": st.session_state.pdf_name,
                    "Topic": focus_topic if focus_topic else "Entire PDF",
                    "Score": f"{score}/{len(quiz)} {emoji}",
                    "Total Time": f"{round(time_taken, 1)} sec",
                    "Avg Time/Qn": f"{round(avg_time_per_q, 1)} sec",
                }
                st.session_state.quiz_history.append(history_entry)

                st.session_state.final_score = score
                st.session_state.final_emoji = emoji
                st.session_state.quiz_submitted = True
                st.rerun()

        if st.session_state.quiz_submitted:
            st.success(
                f"### Quiz Completed! Your Score: {st.session_state.final_score} / {len(quiz)} {st.session_state.final_emoji}"
            )

            if st.checkbox("View Correct Answers & Explanations"):
                for i, item in enumerate(quiz, 1):
                    user_ans = st.session_state.user_answers.get(i)
                    is_correct = user_ans == item.correct_answer

                    if is_correct:
                        st.info(
                            f"**Q{i}.** {item.question}  \n✅ **Your Answer:** {user_ans}  \n*Explanation:* {item.explanation}"
                        )
                    else:
                        st.error(
                            f"**Q{i}.** {item.question}  \n❌ **Your Answer:** {user_ans}  \n🎯 **Correct Answer:** {item.correct_answer}  \n*Explanation:* {item.explanation}"
                        )

            if st.button("Start New Quiz"):
                st.session_state.quiz_data = None
                st.session_state.quiz_submitted = False
                st.rerun()

with tab_history:
    st.header("📊 User Quiz History")
    if not st.session_state.quiz_history:
        st.info(
            "No quizzes taken yet. Your history will appear here after you submit a quiz."
        )
    else:
        df_history = pd.DataFrame(st.session_state.quiz_history)
        df_history.index = df_history.index + 1
        df_history.index.name = "S.No"

        st.dataframe(df_history, use_container_width=True)

        csv_history = df_history.to_csv().encode("utf-8")
        st.download_button(
            label="📥 Download History CSV",
            data=csv_history,
            file_name="quiz_history.csv",
            mime="text/csv",
        )