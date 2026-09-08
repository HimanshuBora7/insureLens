from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import VectorStore
from app.rag.reranker import rerank


class PolicyRetriever:
    def __init__(
        self,
        embedding_model: EmbeddingModel | None = None,
        vector_store: VectorStore | None = None,
    ):
        self.embedding_model = embedding_model or EmbeddingModel()
        self.vector_store = vector_store or VectorStore()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        document_id: str | None = None,
    ) -> list[dict]:
        query_embedding = self.embedding_model.embed_query(query)

        results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=10,
            document_id=document_id,
        )

        ranked_results = rerank(
            query=query,
            results=results,
            top_k=top_k,
        )

        return ranked_results