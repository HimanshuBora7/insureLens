import pytest
from app.verification.deterministic import (
    normalize, contains, extract_numbers, find_rule, deterministic_check
)

class TestDeterministic:
    def test_normalize(self):
        assert normalize("₹5,000") == "rs5000"
        assert normalize("Rs. 5000") == "rs 5000"
        assert normalize("Upper Case") == "upper case"

    def test_contains(self):
        assert contains("This policy covers ₹5,000 for room rent", "5000") is True
        assert contains("This policy covers ₹5,000", "10000") is False

    def test_extract_numbers(self):
        numbers = extract_numbers("The cost is ₹5,000.50 and rs 1000")
        assert "5000.50" in numbers
        assert "1000" in numbers

    def test_find_rule(self):
        assert find_rule("What is the room rent limit?") == "room_rent"
        assert find_rule("ICU charges?") == "icu_iccu"
        assert find_rule("Tell me about cataract surgery") == "cataract"
        assert find_rule("Random unrelated question") is None

    def test_deterministic_check_pass(self):
        question = "What is the room rent limit?"
        answer = "The room rent limit is 2% of sum insured up to Rs 5000."
        
        result = deterministic_check(question, answer)
        assert result["checked"] is True
        assert result["passed"] is True
        assert len(result["missing"]) == 0
        assert len(result["forbidden_found"]) == 0

    def test_deterministic_check_missing_required(self):
        question = "What is the room rent limit?"
        answer = "The room rent limit is up to Rs 5000."  # Missing 2%
        
        result = deterministic_check(question, answer)
        assert result["checked"] is True
        assert result["passed"] is False
        assert "2%" in result["missing"]

    def test_deterministic_check_forbidden(self):
        question = "What is the room rent limit?"
        answer = "The room rent limit is 2% up to Rs 5000 per 24 hours."
        
        result = deterministic_check(question, answer)
        assert result["checked"] is True
        assert result["passed"] is False
        assert "24 hours" in result["forbidden_found"]

    def test_deterministic_check_invented_numbers(self):
        question = "What is the room rent limit?"
        answer = "The room rent limit is 2% up to Rs 5000. For a sum insured of Rs 500000, it is 10000."
        
        result = deterministic_check(question, answer)
        assert result["checked"] is True
        assert result["passed"] is False
        assert "500000" in result["invented_numbers"]
