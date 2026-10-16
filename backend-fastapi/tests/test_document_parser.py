import pytest
from app.services.document_parser import document_parser

def test_parse_invalid_file():
    with pytest.raises(FileNotFoundError, match="Uploaded document was not found"):
        document_parser.parse_document("nonexistent.pdf", "pdf")
