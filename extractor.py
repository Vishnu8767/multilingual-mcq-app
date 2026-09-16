import PyPDF2

def extract_text(uploaded_file) -> str:
    """Extracts raw text from an uploaded file."""
    text = ""
    try:
        if uploaded_file.name.endswith(".pdf"):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        elif uploaded_file.name.endswith(".txt"):
            text = uploaded_file.getvalue().decode("utf-8")
        else:
            text = "Unsupported file type. Please use PDF or TXT."
    except Exception as e:
        text = f"Error extracting text: {e}"
    
    return text