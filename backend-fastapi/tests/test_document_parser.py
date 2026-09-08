import pytest
from app.services.document_parser import document_parser

def test_parse_invalid_file():
    result = document_parser.parse_document("nonexistent.pdf", "pdf")
    assert result == ""
