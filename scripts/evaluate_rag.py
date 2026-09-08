import json

from app.rag.retriever import PolicyRetriever
from app.rag.prompt_builder import build_policy_prompt
from app.llm.ollama_client import OllamaClient


def main():

    with open(
        "data/evaluation/questions.json",
        "r",
        encoding="utf-8",
    ) as file:
        questions = json.load(file)

    retriever = PolicyRetriever()
    client = OllamaClient()

    results = []

    for item in questions:

        question = item["question"]

        print("\n" + "=" * 70)
        print(f"{item['id']}: {question}")
        print("=" * 70)

        # Retrieve evidence
        chunks = retriever.retrieve(
            query=question,
            top_k=5,
        )

        print("\nRetrieved pages:")

        for chunk in chunks:
            print(
                f"Page {chunk['page']} "
                f"(score={chunk['score']:.4f})"
            )

        # Build grounded prompt
        prompt = build_policy_prompt(
            question=question,
            retrieved_chunks=chunks,
        )

        # Generate answer
        answer = client.generate(prompt)

        print("\nAnswer:")
        print(answer)

        results.append(
            {
                "id": item["id"],
                "question": question,
                "retrieved_pages": [
                    chunk["page"] for chunk in chunks
                ],
                "answer": answer,
            }
        )

    with open(
        "data/evaluation/baseline_results.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\n")
    print("=" * 70)
    print("Evaluation complete.")
    print("Results saved to:")
    print("data/evaluation/baseline_results.json")
    print("=" * 70)


if __name__ == "__main__":
    main()