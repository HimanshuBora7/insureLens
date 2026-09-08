from app.rag.pdf_loader import load_pdf
from app.rag.chunker import chunk_text


PDF_PATH = "data/policies/health_policy.pdf"


pages = load_pdf(PDF_PATH)
chunks = chunk_text(pages)

print(f"Total pages: {len(pages)}")
print(f"Total chunks: {len(chunks)}")


# Show chunks around the actual Coverage section.
for i, chunk in enumerate(chunks):

    if 10 <= chunk["page"] <= 16:

        print("\n" + "=" * 70)
        print(f"CHUNK {i + 1}")
        print(f"PAGE: {chunk['page']}")
        print(f"SECTION: {chunk.get('section', 'Unknown Section')}")
        print("=" * 70)
        print(chunk["text"])