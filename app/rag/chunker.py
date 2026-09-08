import re


MAJOR_SECTIONS = {
    "1": "Preamble",
    "2": "Operative Clause",
    "3": "Definitions",
    "4": "Coverage",
    "5": "Renewal Benefit",
    "6": "Waiting Period",
    "7": "Exclusions",
    "8": "Moratorium Period",
    "9": "Claim Procedure",
    "10": "General Terms And Conditions",
    "11": "Redressal of Grievance",
    "12": "Table of Benefits",
    "13": "Annexure A",
    "14": "Annexure B",
    "15": "Flexi OP Care",
    "16": "Home Care Treatment",
}


def clean_line(line: str) -> str:
    """Normalize whitespace from PDF extraction."""
    return re.sub(r"\s+", " ", line).strip()


def is_toc_line(line: str) -> bool:
    """Detect Table of Contents entries."""
    return bool(
        re.search(r"\.{3,}\s*\d+\s*$", line)
    )


def detect_section(
    line: str,
    current_section: str,
) -> str:
    """
    Detect a valid major policy section.

    Only known major sections are accepted.
    This prevents numbered notes such as:
        2. In case of admission...
    from being incorrectly treated as a new section.
    """

    line = clean_line(line)

    if not line:
        return current_section

    # Ignore PDF page headers / footers.
    if re.match(
        r"^PAGE\s+\d+\s+OF\s+\d+$",
        line,
        re.IGNORECASE,
    ):
        return current_section

    # Ignore UIN lines.
    if line.startswith("UIN:"):
        return current_section

    # Ignore Table of Contents entries.
    if is_toc_line(line):
        return current_section

    # --------------------------------------------------
    # Major section detection
    #
    # Examples:
    #   4. COVERAGE
    #   4. Coverage
    #   10. General Terms And Conditions
    #
    # Important:
    # A numbered line is only considered a major section
    # if its title matches our known MAJOR_SECTIONS list.
    # --------------------------------------------------

    major_match = re.match(
        r"^(\d+)\.\s+(.+)$",
        line,
    )

    if major_match:
        number = major_match.group(1)
        title = major_match.group(2).strip()

        expected_title = MAJOR_SECTIONS.get(number)

        if expected_title:
            normalized_title = re.sub(
                r"[^a-z0-9]+",
                " ",
                title.lower(),
            ).strip()

            normalized_expected = re.sub(
                r"[^a-z0-9]+",
                " ",
                expected_title.lower(),
            ).strip()

            # Only accept the heading if it resembles the
            # expected major-section title.
            if (
                normalized_title == normalized_expected
                or normalized_expected in normalized_title
                or normalized_title in normalized_expected
            ):
                return f"{number}. {title}"

    # This is NOT a new section.
    # Preserve the existing section.
    return current_section


def chunk_text(
    pages: list[dict],
    chunk_size: int = 700,
    chunk_overlap: int = 150,
) -> list[dict]:

    chunks = []

    # Keep the section across page boundaries.
    current_section = "Unknown Section"

    for page in pages:

        page_number = page["page"]
        text = page["text"]

        if not text.strip():
            continue

        lines = text.splitlines()
        current_text = ""

        for raw_line in lines:

            line = clean_line(raw_line)

            if not line:
                continue

            # Detect section before adding the line.
            detected_section = detect_section(
                line,
                current_section,
            )

            if detected_section != current_section:
                current_section = detected_section

            current_text += line + "\n"

            # Create chunk when target size is reached.
            if len(current_text) >= chunk_size:

                chunk = current_text.strip()

                if chunk:
                    chunks.append(
                        {
                            "text": chunk,
                            "page": page_number,
                            "section": current_section,
                        }
                    )

                # Keep overlap for context continuity.
                current_text = current_text[-chunk_overlap:]

        # Add remaining text from the page.
        if current_text.strip():

            chunks.append(
                {
                    "text": current_text.strip(),
                    "page": page_number,
                    "section": current_section,
                }
            )

    return chunks