# core/pdf_utils.py

import re
from PyPDF2 import PdfReader
import fitz  # PyMuPDF


def read_pdf_text(file):
    """
    Försöker extrahera text från en PDF med PyPDF2, och faller tillbaka till PyMuPDF (fitz) vid behov.
    """
    # Försök med PyPDF2
    try:
        pdf = PdfReader(file)
        text = ''.join(page.extract_text() or '' for page in pdf.pages)
        if text.strip():
            print("✅ Text extraherad med PyPDF2")
            return text
    except Exception as e:
        print("❌ PyPDF2 misslyckades:", e)

    # Fallback: fitz
    try:
        print("🔁 Fallback till fitz (PyMuPDF)")
        file.seek(0)  # Viktigt! Vi måste söka om efter PyPDF2
        doc = fitz.open(stream=file.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in doc])
    except Exception as e:
        print("❌ fitz också misslyckades:", e)

    return ""


def normalize_pdf_text(text):
    """
    Rensar PDF-text från konstiga mellanrum, radbrytningar m.m.
    """
    text = re.sub(r'[ ]{2,}', ' ', text)  # Ta bort överflödiga mellanslag
    text = re.sub(r'(?<=\w)[ ](?=\w)', '', text)  # T e x t → Text
    text = re.sub(r'\n{2,}', '\n', text)  # Max 1 radbrytning i rad
    return text.strip()
