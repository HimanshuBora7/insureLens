import pytest
from app.rag.reranker import tokenize, rerank

class TestReranker:
    def test_tokenize(self):
        tokens = tokenize("This is a ₹5000 test!")
        assert "this" in tokens
        assert "is" in tokens
        assert "a" in tokens
        assert "₹5000" in tokens
        assert "test" in tokens

    def test_rerank_empty(self):
        results = {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        ranked = rerank("query", results)
        assert len(ranked) == 0

    def test_rerank_scoring_and_sorting(self):
        query = "health insurance coverage"
        
        results = {
            "documents": [[
                "health insurance coverage for individuals",
                "completely unrelated text",
                "some health coverage details"
            ]],
            "metadatas": [[
                {"page": 1, "section": "1. Coverage"},
                {"page": 2, "section": "Unknown Section"},
                {"page": 3, "section": "1. Coverage"}
            ]],
            "distances": [[0.1, 0.9, 0.4]]
        }

        ranked = rerank(query, results, top_k=3)
        
        assert len(ranked) == 3
        # The best match (highest overlap and lowest distance) should be first
        assert ranked[0]["text"] == "health insurance coverage for individuals"
        # The next should be the one with partial overlap and medium distance
        assert ranked[1]["text"] == "some health coverage details"
        # The worst match should be last
        assert ranked[2]["text"] == "completely unrelated text"

    def test_rerank_top_k(self):
        query = "health"
        
        results = {
            "documents": [["doc1", "doc2", "doc3", "doc4"]],
            "metadatas": [[{"page": 1}, {"page": 1}, {"page": 1}, {"page": 1}]],
            "distances": [[0.1, 0.2, 0.3, 0.4]]
        }

        ranked = rerank(query, results, top_k=2)
        assert len(ranked) == 2
