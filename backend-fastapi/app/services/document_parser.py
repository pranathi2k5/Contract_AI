import os
import tempfile

import PyPDF2
import docx
import pytesseract
from PIL import Image

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
            raise ValueError(f"Could not read PDF: {e}") from e
        if text.strip():
            return text

        try:
            import fitz
        except ImportError as e:
            raise ValueError("PDF contains no selectable text and PDF OCR is unavailable.") from e

        try:
            with fitz.open(file_path) as pdf:
                ocr_pages = []
                for page in pdf:
                    pixmap = page.get_pixmap(dpi=180, alpha=False)
                    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
                    ocr_pages.append(pytesseract.image_to_string(image))
                text = "\n".join(ocr_pages)
        except Exception as e:
            raise ValueError(f"Could not extract text from PDF with OCR: {e}") from e
        if not text.strip():
            raise ValueError("No text could be extracted from the PDF, including with OCR.")
        return text

    @staticmethod
    def parse_docx(file_path: str) -> str:
        try:
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            raise ValueError(f"Could not read DOCX: {e}") from e

    @staticmethod
    def parse_txt(file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Could not read text document: {e}") from e

    @staticmethod
    def parse_image(file_path: str) -> str:
        try:
            image = Image.open(file_path)
            return pytesseract.image_to_string(image)
        except Exception as e:
            raise ValueError(f"Could not extract text from image with OCR: {e}") from e

    @staticmethod
    def normalize_file_type(file_type: str, filename: str = "") -> str:
        raw = (file_type or "").upper().lstrip(".")
        if not raw and filename:
            raw = os.path.splitext(filename)[1].upper().lstrip(".")
        if raw in {"PNG", "JPG", "JPEG", "TIF", "TIFF", "WEBP"}:
            return "IMAGE"
        if raw in {"TXT", "TEXT"}:
            return "TXT"
        if raw in {"DOCX", "DOC"}:
            return "DOCX"
        if raw:
            return raw
        return "PDF"

    @staticmethod
    def parse_document(file_path: str, file_type: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Uploaded document was not found: {file_path}")
        file_type = DocumentParser.normalize_file_type(file_type, file_path)
        if file_type == "PDF":
            return DocumentParser.parse_pdf(file_path)
        if file_type == "DOCX":
            return DocumentParser.parse_docx(file_path)
        if file_type == "TXT":
            return DocumentParser.parse_txt(file_path)
        if file_type == "IMAGE":
            return DocumentParser.parse_image(file_path)
        raise ValueError(f"Unsupported document type for extraction: {file_type}")

    @staticmethod
    def parse_bytes(content: bytes, file_type: str, filename: str = "") -> str:
        suffix = os.path.splitext(filename or "")[1] or f".{file_type or 'bin'}"
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        try:
            with open(path, "wb") as tmp:
                tmp.write(content)
            return DocumentParser.parse_document(path, DocumentParser.normalize_file_type(file_type, filename))
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


document_parser = DocumentParser()
