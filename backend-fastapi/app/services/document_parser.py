import PyPDF2
import docx
import pytesseract
from PIL import Image
import os

class DocumentParser:
    @staticmethod
    def parse_pdf(file_path: str) -> str:
        text = ""
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return text

    @staticmethod
    def parse_docx(file_path: str) -> str:
        try:
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            print(f"Error reading DOCX: {e}")
            return ""

    @staticmethod
    def parse_image(file_path: str) -> str:
        try:
            image = Image.open(file_path)
            return pytesseract.image_to_string(image)
        except Exception as e:
            print(f"Error OCR image: {e}")
            return ""

    @staticmethod
    def parse_document(file_path: str, file_type: str) -> str:
        if not os.path.exists(file_path):
            return ""
        file_type = file_type.upper()
        if file_type == 'PDF':
            return DocumentParser.parse_pdf(file_path)
        elif file_type == 'DOCX':
            return DocumentParser.parse_docx(file_path)
        elif file_type == 'IMAGE':
            return DocumentParser.parse_image(file_path)
        return ""

document_parser = DocumentParser()
