from app.rag.pdf_loader import load_pdf


def main():
    pdf_path = "data/policies/health_policy.pdf"

    pages = load_pdf(pdf_path)

    print(f"Total PDF pages: {len(pages)}")
    print(f"Pages containing text: {sum(bool(p['text']) for p in pages)}")

    for page in pages[:5]:
        print("\n" + "=" * 60)
        print(f"PDF PAGE {page['page']}")
        print("=" * 60)

        if page["text"]:
            print(page["text"][:1000])
        else:
            print("[NO EXTRACTABLE TEXT]")


if __name__ == "__main__":
    main()