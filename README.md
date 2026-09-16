# 🌐 Multilingual MCQ App

An AI-based academic study tool that helps students generate **Multiple Choice Questions (MCQs)** and **summaries** from their study materials.

## 📌 About the Project

The **Multilingual MCQ App** is an academic application developed using **Python, Streamlit, and Google Gemini AI**. It allows students to upload their study materials and automatically generate useful summaries and MCQs.

The main aim of this project is to **save students' time and make exam preparation easier**.

## ✨ Features

- 📄 Upload **PDF and Word documents**
- 🤖 Generate **MCQs using Google Gemini AI**
- 📝 Generate **summaries from study materials**
- 🌐 Support for **multiple languages**
- 📚 Generate questions based on the uploaded content
- 💻 Supports technical content such as **programming, algorithms, and formulas**
- ✅ Uses **Pydantic** to validate generated output
- 🎯 Useful for **exam and lab preparation**
- 🖥️ Simple and user-friendly **Streamlit interface**

## 🛠️ Technologies Used

- Python
- Streamlit
- Google Gemini API
- Pydantic
- PDF Processing
- Python-docx
- Markdown
- LaTeX

## 🏗️ System Workflow

```text
        Study Material
              ↓
       Upload PDF / Word
              ↓
        Text Extraction
              ↓
       Google Gemini AI
              ↓
      ┌────────┴────────┐
      ↓                 ↓
   Summary             MCQs
      ↓                 ↓
      └────────┬────────┘
               ↓
       Output Validation
               ↓
      Display in Streamlit
      
