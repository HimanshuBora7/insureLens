from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import VectorStore
from app.rag.reranker import rerank


def main():
    query = "What is the room rent limit?"

    print(f"\nQuery: {query}\n")

    embedding_model = EmbeddingModel()
    vector_store = VectorStore()

    query_embedding = embedding_model.embed_query(query)

    results = vector_store.search(
        query_embedding=query_embedding,
        n_results=10,
    )

    ranked_results = rerank(
        query=query,
        results=results,
        top_k=5,
    )

    for i, result in enumerate(
        ranked_results,
        start=1,
    ):
        print("=" * 70)
        print(f"RESULT {i}")
        print(f"PAGE: {result['page']}")
        print(f"VECTOR DISTANCE: {result['distance']:.4f}")
        print(f"RERANK SCORE: {result['score']:.4f}")
        print("=" * 70)
        print(result["text"])
        print()


if __name__ == "__main__":
    main()