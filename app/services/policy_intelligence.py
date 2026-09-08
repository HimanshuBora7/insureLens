import json
import re

from app.llm.ollama_client import OllamaClient
from app.rag.prompt_builder import build_intelligence_prompt
from app.rag.retriever import PolicyRetriever

INTELLIGENCE_QUERIES = [
    "Table of Benefits room rent ICU cataract sub-limit co-payment",
    "room rent boarding nursing expenses per day limit",
    "ICU ICCU room charge limit",
    "cataract treatment sub-limit",
    "waiting period pre-existing diseases specified diseases 36 months",
    "co-payment copayment 5% risk based",
    "exclusions what is not covered",
    "sum insured hospitalisation expenses coverage",
    "deductible excess amount",
]

CATEGORIES = [
    "coverage",
    "important_clauses",
    "potential_concerns",
    "exclusions",
    "waiting_periods",
    "copayment",
    "deductibles",
    "sub_limits",
]

REVIEW_TRIGGERS = [
    "careful about",
    "watch out",
    "watch for",
    "unfavourable",
    "unfavorable",
    "red flag",
    "things to watch",
    "summarise this policy",
    "summarize this policy",
    "what should i know",
    "important clauses",
    "potential concern",
    "review this policy",
    "key conditions",
]


def is_policy_review_question(question: str) -> bool:
    q = question.lower()
    return any(trigger in q for trigger in REVIEW_TRIGGERS)


def parse_json_object(text: str) -> dict:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Model did not return JSON.")

    return json.loads(cleaned[start:end + 1])


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("₹", "rs")
    text = text.replace(",", "")
    text = text.replace("rs.", "rs")
    return text


def extract_numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", normalize(text)))


def merge_chunks(chunk_lists: list[list[dict]], limit: int = 14) -> list[dict]:
    merged = []
    seen = set()

    for chunks in chunk_lists:
        for chunk in chunks:
            key = (chunk["page"], chunk["text"][:160])

            if key in seen:
                continue

            seen.add(key)
            merged.append(chunk)

            if len(merged) >= limit:
                return merged

    return merged


def attach_sources(item: dict, chunks: list[dict]) -> dict | None:
    source_ids = item.get("source_ids") or []
    sources = []
    cited_text = []

    for raw_id in source_ids:
        try:
            index = int(raw_id)
        except (TypeError, ValueError):
            continue

        if index < 1 or index > len(chunks):
            continue

        chunk = chunks[index - 1]
        sources.append(
            {
                "page": chunk["page"],
                "section": chunk.get("section", "Unknown Section"),
            }
        )
        cited_text.append(chunk["text"])

    if not sources:
        return None

    label = str(item.get("label") or "").strip()
    detail = str(item.get("detail") or "").strip()

    if not label or not detail:
        return None

    combined_claim = f"{label} {detail}"
    claim_numbers = extract_numbers(combined_claim)
    evidence = normalize(" ".join(cited_text))
    missing = [n for n in claim_numbers if n not in evidence]

    grounded = len(missing) == 0

    result = {
        "label": label,
        "detail": detail,
        "sources": sources,
        "grounded": grounded,
    }

    why = str(item.get("why_it_matters") or "").strip()

    if why:
        result["why_it_matters"] = why

    if missing:
        result["unsupported_numbers"] = missing

    return result


class PolicyIntelligence:

    def __init__(
        self,
        retriever: PolicyRetriever | None = None,
        llm: OllamaClient | None = None,
    ):
        self.retriever = retriever or PolicyRetriever()
        self.llm = llm or OllamaClient()

    def collect_evidence(
        self,
        document_id: str | None = None,
    ) -> list[dict]:
        chunk_lists = []

        for query in INTELLIGENCE_QUERIES:
            chunk_lists.append(
                self.retriever.retrieve(
                    query=query,
                    top_k=3,
                    document_id=document_id,
                )
            )

        return merge_chunks(chunk_lists, limit=16)

    def summarize(
        self,
        document_id: str | None = None,
    ) -> dict:
        retrieved_chunks = self.collect_evidence(document_id)

        if not retrieved_chunks:
            return {
                "briefing": {category: [] for category in CATEGORIES},
                "sources": [],
                "verification": {
                    "grounded": False,
                    "citation_supported": False,
                    "confidence": 0.0,
                    "action": "REVIEW",
                    "unsupported_claims": [
                        "No relevant policy evidence found."
                    ],
                },
            }

        prompt = build_intelligence_prompt(retrieved_chunks)
        raw = self.llm.generate(prompt)

        try:
            parsed = parse_json_object(raw)
        except (ValueError, json.JSONDecodeError):
            return {
                "briefing": {category: [] for category in CATEGORIES},
                "sources": unique_sources(retrieved_chunks),
                "verification": {
                    "grounded": False,
                    "citation_supported": False,
                    "confidence": 0.0,
                    "action": "REVIEW",
                    "unsupported_claims": [
                        "Intelligence model returned invalid JSON."
                    ],
                },
            }

        briefing = {}
        dropped = []
        kept_grounded = 0
        kept_total = 0

        for category in CATEGORIES:
            cleaned = []

            for item in parsed.get(category) or []:
                attached = attach_sources(item, retrieved_chunks)

                if attached is None:
                    dropped.append(
                        f"{category}: missing evidence for {item.get('label')}"
                    )
                    continue

                kept_total += 1

                if not attached["grounded"]:
                    dropped.append(
                        f"{attached['label']}: numbers not found in cited evidence"
                    )
                    continue

                kept_grounded += 1
                cleaned.append(attached)

            briefing[category] = cleaned[:5]

        confidence = (
            kept_grounded / kept_total if kept_total else 0.0
        )
        grounded = kept_total > 0 and kept_grounded == kept_total

        if grounded:
            action = "ACCEPT"
        elif kept_grounded > 0:
            action = "REVIEW"
        else:
            action = "REVIEW"

        return {
            "briefing": finalize_briefing(briefing),
            "sources": unique_sources(retrieved_chunks),
            "verification": {
                "grounded": grounded,
                "citation_supported": kept_total > 0,
                "confidence": round(confidence, 2),
                "action": action,
                "unsupported_claims": dropped[:8],
            },
        }


def derive_potential_concerns(briefing: dict) -> list[dict]:
    existing = list(briefing.get("potential_concerns") or [])

    if existing:
        return existing[:5]

    derived = []
    templates = [
        (
            "copayment",
            "You may have to pay this share of an otherwise eligible claim yourself.",
        ),
        (
            "waiting_periods",
            "Related claims may not be payable until this waiting period is over.",
        ),
        (
            "sub_limits",
            "The insurer may cap this benefit below the overall cover.",
        ),
        (
            "important_clauses",
            "This condition can reduce what you receive even when a claim is otherwise eligible.",
        ),
    ]

    for category, why in templates:
        for item in briefing.get(category) or []:
            derived.append(
                {
                    "label": item["label"],
                    "detail": item["detail"],
                    "why_it_matters": why,
                    "sources": item["sources"],
                    "grounded": True,
                }
            )

    return derived[:5]


def backfill_categories(briefing: dict) -> dict:
    pool = []

    for category in CATEGORIES:
        pool.extend(briefing.get(category) or [])

    def matching(keywords: list[str]) -> list[dict]:
        found = []
        seen = set()

        for item in pool:
            blob = f"{item['label']} {item['detail']}".lower()
            if any(keyword in blob for keyword in keywords):
                key = (item["label"], item["detail"])
                if key not in seen:
                    seen.add(key)
                    found.append(item)

        return found[:5]

    if not briefing.get("waiting_periods"):
        briefing["waiting_periods"] = matching(["waiting period", "waiting"])

    if not briefing.get("copayment"):
        briefing["copayment"] = matching(["co-payment", "copayment", "co-pay"])

    if not briefing.get("sub_limits"):
        briefing["sub_limits"] = matching(
            ["room rent", "icu", "cataract", "sub-limit", "sub limit"]
        )

    if not briefing.get("exclusions"):
        briefing["exclusions"] = matching(["exclusion", "not covered", "excluded"])

    return briefing


def finalize_briefing(briefing: dict) -> dict:
    briefing = backfill_categories(briefing)
    briefing["potential_concerns"] = derive_potential_concerns(briefing)
    return briefing


def unique_sources(chunks: list[dict]) -> list[dict]:
    sources = []
    seen = set()

    for chunk in chunks:
        page = chunk["page"]
        section = chunk.get("section", "Unknown Section")
        key = (page, section)

        if key in seen:
            continue

        seen.add(key)
        sources.append({"page": page, "section": section})

    return sources


def briefing_to_answer(briefing: dict) -> str:
    lines = [
        "Here is what you should pay attention to in this policy, "
        "based only on retrieved clauses."
    ]

    coverage = briefing.get("coverage") or []

    if coverage:
        lines.append("\n**Coverage**")
        for item in coverage:
            lines.append(f"- {item['label']}: {item['detail']}")

    clauses = briefing.get("important_clauses") or []

    if clauses:
        lines.append("\n**Important clauses**")
        for item in clauses:
            lines.append(f"- {item['label']}: {item['detail']}")

    concerns = briefing.get("potential_concerns") or []

    if concerns:
        lines.append("\n**Potential concerns**")
        for item in concerns:
            lines.append(f"- {item['label']}: {item['detail']}")
            if item.get("why_it_matters"):
                lines.append(f"  {item['why_it_matters']}")

    if len(lines) == 1:
        lines.append(
            "\nThe retrieved evidence was not enough to build a briefing."
        )

    return "\n".join(lines)
