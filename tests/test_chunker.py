import pytest
from app.rag.chunker import clean_line, is_toc_line, detect_section, chunk_text

class TestChunker:
    def test_clean_line(self):
        assert clean_line("  Hello   World  \n") == "Hello World"
        assert clean_line("") == ""
        assert clean_line("Already clean") == "Already clean"

    def test_is_toc_line(self):
        assert is_toc_line("4. Coverage ... 12") is True
        assert is_toc_line("Section 1 ..................... 5") is True
        assert is_toc_line("Just some text") is False
        assert is_toc_line("Not a toc ...") is False

    def test_detect_section(self):
        # Known major sections from MAJOR_SECTIONS
        # "4": "Coverage"
        assert detect_section("4. Coverage", "Unknown Section") == "4. Coverage"
        assert detect_section("4. COVERAGE", "Unknown Section") == "4. COVERAGE"
        
        # Unknown section or not in MAJOR_SECTIONS
        assert detect_section("99. Random Section", "Current Section") == "Current Section"
        
        # PDF headers/footers
        assert detect_section("PAGE 1 OF 10", "Current Section") == "Current Section"
        
        # UIN lines
        assert detect_section("UIN: ABC12345", "Current Section") == "Current Section"

    def test_chunk_text(self):
        pages = [
            {"page": 1, "text": "4. Coverage\nThis is the coverage section. " * 30},
        ]
        chunks = chunk_text(pages, chunk_size=100, chunk_overlap=20)
        
        assert len(chunks) > 0
        assert chunks[0]["page"] == 1
        # The section should be detected as 4. Coverage
        assert chunks[0]["section"] == "4. Coverage"

    def test_chunk_text_empty_pages(self):
        pages = [{"page": 1, "text": "   \n  "}, {"page": 2, "text": ""}]
        chunks = chunk_text(pages)
        assert len(chunks) == 0
