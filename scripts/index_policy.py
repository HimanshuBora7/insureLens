from app.rag.pdf_loader import load_pdf
from app.rag.chunker import chunk_text
from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import VectorStore


def main():
    pdf_path = "data/policies/health_policy.pdf"

    print("Loading PDF...")
    pages = load_pdf(pdf_path)

    print(f"Loaded {len(pages)} pages")

    print("\nCreating chunks...")
    chunks = chunk_text(pages)

    print(f"Created {len(chunks)} chunks")

    print("\nLoading embedding model...")
    embedding_model = EmbeddingModel()

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    print("\nCreating embeddings...")
    embeddings = embedding_model.embed_documents(texts)

    print("\nStoring embeddings in Chroma...")
    vector_store = VectorStore()

    vector_store.add_chunks(
        chunks,
        embeddings,
        document_id="health_policy",
    )

    print("\nIndexing complete!")
    print(f"Stored {len(chunks)} chunks.")


if __name__ == "__main__":
    main()