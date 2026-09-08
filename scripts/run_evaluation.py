import json
from pathlib import Path

from app.rag.retriever import PolicyRetriever
from app.rag.prompt_builder import build_policy_prompt
from app.llm.ollama_client import OllamaClient


def main():

    questions_path = Path(
        "data/evaluation/questions.json"
    )

    output_path = Path(
        "data/evaluation/current_results.json"
    )

    with open(
        questions_path,
        "r",
        encoding="utf-8",
    ) as f:
        questions = json.load(f)

    print("\n" + "=" * 70)
    print("INSURELENS FRESH EVALUATION")
    print("=" * 70)

    retriever = PolicyRetriever()
    llm = OllamaClient()

    results = []

    for item in questions:

        question_id = item["id"]
        question = item["question"]

        print("\n" + "-" * 70)
        print(f"{question_id.upper()}: {question}")
        print("-" * 70)

        retrieved_chunks = retriever.retrieve(
            question
        )

        prompt = build_policy_prompt(
            question,
            retrieved_chunks,
        )

        answer = llm.generate(prompt)

        print("\nANSWER:")
        print(answer)

        results.append(
            {
                "id": question_id,
                "question": question,
                "answer": answer,
            }
        )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("\n" + "=" * 70)
    print("FRESH EVALUATION COMPLETE")
    print("=" * 70)
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()