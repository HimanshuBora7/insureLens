"""
Shared fixtures for the InsureLens test suite.
"""

import pytest

from app.rag.embeddings import EmbeddingModel


# ── Embedding model (session-scoped to avoid reloading) ────────────


@pytest.fixture(scope="session")
def embedding_model():
    """Load the embedding model once for the entire test session."""
    return EmbeddingModel()


# ── Sample pages for chunker tests ─────────────────────────────────


@pytest.fixture()
def sample_pages():
    """Multi-page document with known sections and content."""
    return [
        {
            "page": 1,
            "text": (
                "4. Coverage\n"
                "This policy covers hospitalisation expenses.\n"
                "Room rent is capped at 2% of the Sum Insured.\n"
            ),
        },
        {
            "page": 2,
            "text": (
                "7. Exclusions\n"
                "Pre-existing conditions are excluded for 36 months.\n"
                "Cosmetic treatments are not covered.\n"
            ),
        },
    ]


@pytest.fixture()
def empty_pages():
    """Pages with whitespace-only or empty text."""
    return [
        {"page": 1, "text": ""},
        {"page": 2, "text": "   \n   \n   "},
    ]


# ── Reranker results fixture ───────────────────────────────────────


@pytest.fixture()
def reranker_results():
    """Chroma-style results dict for reranker tests."""
    return {
        "documents": [
            [
                "Room rent is limited to 2% of Sum Insured or Rs 5000.",
                "ICU charges are capped at 5% of Sum Insured.",
                "The waiting period for pre-existing diseases is 36 months.",
            ]
        ],
        "metadatas": [
            [
                {"page": 3, "section": "4. Coverage"},
                {"page": 4, "section": "4. Coverage"},
                {"page": 6, "section": "6. Waiting Period"},
            ]
        ],
        "distances": [
            [0.25, 0.55, 0.80],
        ],
    }


# ── Deterministic check fixtures ───────────────────────────────────


@pytest.fixture()
def room_rent_question():
    return "What is the room rent limit?"


@pytest.fixture()
def room_rent_good_answer():
    return (
        "Room rent is capped at 2% of Sum Insured "
        "or Rs. 5,000 per day, whichever is lower."
    )


@pytest.fixture()
def room_rent_bad_answer_missing():
    return "Room rent is capped at 2% of Sum Insured."


@pytest.fixture()
def room_rent_bad_answer_forbidden():
    return (
        "Room rent is capped at 2% of Sum Insured "
        "or Rs. 5,000 per day. Minimum 24 hours stay required."
    )
