from app.rag.retriever import PolicyRetriever
from app.verification.verifier import PolicyVerifier


def main():

    question = "What is the room rent limit?"

    # This deliberately contains a potentially unsupported claim.
    answer = """
The room rent limit is up to 2% of the Sum Insured,
subject to a maximum of Rs 5,000 per day.

The room rent is also subject to a minimum hospitalization
period of 24 consecutive hours.
"""

    retriever = PolicyRetriever()

    chunks = retriever.retrieve(
        query=question,
        top_k=5,
    )

    verifier = PolicyVerifier()

    result = verifier.verify(
        question=question,
        answer=answer,
        retrieved_chunks=chunks,
    )

    print("\n" + "=" * 70)
    print("VERIFICATION RESULT")
    print("=" * 70)

    print(result)


if __name__ == "__main__":
    main()