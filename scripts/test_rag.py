from app.rag.retriever import PolicyRetriever
from app.rag.prompt_builder import build_policy_prompt
from app.llm.ollama_client import OllamaClient


def main():

    question = "What is the ICU and ICCU room charge limit?"

    print(f"\nQuestion: {question}\n")

    # Retrieve relevant policy chunks
    retriever = PolicyRetriever()

    chunks = retriever.retrieve(
        query=question,
        top_k=5,
    )

    print("Retrieved sources:")

    for i, chunk in enumerate(chunks, start=1):
        print(
            f"{i}. Page {chunk['page']} "
            f"| Section: {chunk.get('section', 'Unknown Section')} "
            f"| Score: {chunk['score']:.4f}"
        )

    # Build grounded prompt
    prompt = build_policy_prompt(
        question=question,
        retrieved_chunks=chunks,
    )

    # Ask local LLM
    client = OllamaClient()

    answer = client.generate(prompt)

    # --------------------------------------------------
    # Application-controlled citation
    # --------------------------------------------------

    best_source = chunks[0]

    source_page = best_source["page"]
    source_section = best_source.get(
        "section",
        "Unknown Section",
    )

    print("\n" + "=" * 70)
    print("INSURELENS ANSWER")
    print("=" * 70)

    print(answer)

    print("\n" + "-" * 70)
    print(
        f"Verified Source: "
        f"Page {source_page} — {source_section}"
    )


if __name__ == "__main__":
    main()