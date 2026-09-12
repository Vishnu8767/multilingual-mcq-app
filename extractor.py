import fitz  # PyMuPDF
def extract_text_from_pdf(uploaded_file, max_pages: int = 15) -> str:
    """Extracts raw UTF-8 text from an uploaded PDF stream."""
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    extracted_text = []

    pages_to_read = min(len(doc), max_pages)

    for page_num in range(pages_to_read):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        if text.strip():
            extracted_text.append(text.strip())

    return "\n\n".join(extracted_text)