import json
from pathlib import Path

from app.rag.chunker import chunk_text
from app.rag.embeddings import EmbeddingModel
from app.rag.pdf_loader import load_pdf
from app.rag.vector_store import VectorStore

UPLOAD_DIR = Path("data/uploads")


class PolicyIndexer:

    def __init__(
        self,
        embedding_model: EmbeddingModel | None = None,
        vector_store: VectorStore | None = None,
    ):
        self.embedding_model = embedding_model or EmbeddingModel()
        self.vector_store = vector_store or VectorStore()
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def index_upload(
        self,
        file_bytes: bytes,
        filename: str,
        document_id: str,
    ) -> dict:
        pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
        pdf_path.write_bytes(file_bytes)

        pages = load_pdf(str(pdf_path))
        chunks = chunk_text(pages)

        if not chunks:
            raise ValueError(
                "No text could be extracted from this PDF."
            )

        embeddings = self.embedding_model.embed_documents(
            [chunk["text"] for chunk in chunks]
        )

        self.vector_store.delete_document(document_id)
        self.vector_store.add_chunks(
            chunks,
            embeddings,
            document_id=document_id,
        )

        meta = {
            "document_id": document_id,
            "filename": filename,
            "pages": len(pages),
            "chunks": len(chunks),
        }

        meta_path = UPLOAD_DIR / f"{document_id}.json"
        meta_path.write_text(
            json.dumps(meta, indent=2),
            encoding="utf-8",
        )

        return meta

    def get_meta(self, document_id: str) -> dict | None:
        meta_path = UPLOAD_DIR / f"{document_id}.json"

        if not meta_path.exists():
            return None

        return json.loads(
            meta_path.read_text(encoding="utf-8")
        )
