import re


def tokenize(text: str) -> set[str]:
    return set(
        re.findall(r"\b[a-zA-Z0-9₹]+\b", text.lower())
    )


def rerank(
    query: str,
    results: dict,
    top_k: int = 5,
) -> list[dict]:

    query_tokens = tokenize(query)

    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    if not documents:
        return []

    ranked = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances,
    ):
        document_tokens = tokenize(document)

        keyword_overlap = len(
            query_tokens.intersection(document_tokens)
        )

        semantic_score = 1 / (1 + distance)

        final_score = (
            semantic_score * 0.7
            + keyword_overlap * 0.1
        )

        ranked.append(
            {
                "text": document,
                "page": metadata["page"],
                "section": metadata.get(
                    "section",
                    "Unknown Section"
                ),
                "distance": distance,
                "score": final_score,
            }
        )

    ranked.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return ranked[:top_k]