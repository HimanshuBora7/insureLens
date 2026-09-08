import pymupdf


def load_pdf(file_path: str) -> list[dict]:
    """
    Extract text from a PDF while preserving PDF page numbers.
    """
    document = pymupdf.open(file_path)

    pages = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text()

        pages.append(
            {
                "page": page_number,
                "text": text.strip(),
            }
        )

    document.close()

    return pages