
import os

import chromadb
from dotenv import load_dotenv

load_dotenv()


class VectorStore:

    def __init__(
        self,
        collection_name: str | None = None,
        persist_directory: str | None = None,
    ):
        self.client = chromadb.PersistentClient(
            path=persist_directory or os.getenv(
                "CHROMA_PERSIST_DIR", "data/chroma"
            )
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name or os.getenv(
                "CHROMA_COLLECTION", "insurance_policies"
            )
        )

    def add_chunks(
        self,
        chunks: list[dict],
        embeddings: list[list[float]],
        document_id: str,
    ):
        ids = [
            f"{document_id}_chunk_{i}"
            for i in range(len(chunks))
        ]

        documents = [
            chunk["text"]
            for chunk in chunks
        ]

        metadatas = [
            {
                "page": chunk["page"],
                "section": chunk.get(
                    "section",
                    "Unknown Section",
                ),
                "document_id": document_id,
            }
            for chunk in chunks
        ]

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding: list[float],
        n_results: int = 10,
        document_id: str | None = None,
    ):
        where = None

        if document_id:
            where = {
                "document_id": {"$eq": document_id}
            }

        empty = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        if self.collection.count() == 0:
            return empty

        available = n_results

        if where is not None:
            matched = self.collection.get(where=where)
            available = min(n_results, len(matched.get("ids") or []))

            if available == 0:
                return empty

        try:
            return self.collection.query(
                query_embeddings=[query_embedding],
                n_results=available,
                where=where,
            )
        except Exception:
            return empty

    def delete_document(self, document_id: str) -> None:
        try:
            self.collection.delete(
                where={"document_id": {"$eq": document_id}}
            )
        except Exception:
            return

