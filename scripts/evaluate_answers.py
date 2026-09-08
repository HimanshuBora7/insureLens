import json
import re
from pathlib import Path


# ---------------------------------------------------------
# Question-specific factual checks
# ---------------------------------------------------------

CHECKS = {
    "q1": {
        "required": ["2%", "5000"],
        "forbidden": [],
        "description": "Room rent must be 2% of Sum Insured, capped at Rs 5,000/day.",
    },
    "q2": {
        "required": ["5%", "10000"],
        "forbidden": ["2%"],
        "description": "ICU/ICCU must be 5% of Sum Insured, capped at Rs 10,000/day.",
    },
    "q3": {
        "required": ["25%", "40000"],
        "forbidden": [],
        "description": "Cataract limit must be 25% of Sum Insured or Rs 40,000, whichever is lower.",
    },
    "q4": {
        "required": ["30"],
        "forbidden": [],
        "description": "Pre-hospitalisation coverage is 30 days.",
    },
    "q5": {
        "required": ["60"],
        "forbidden": [],
        "description": "Post-hospitalisation coverage is 60 days.",
    },
    "q6": {
        "required": ["36"],
        "forbidden": [],
        "description": "Pre-existing disease waiting period is 36 months.",
    },
    "q7": {
        "required": ["5%"],
        "forbidden": [],
        "description": "Standard co-payment is 5%.",
    },
    "q8": {
        "required": ["24"],
        "forbidden": [],
        "description": "Hospitalisation requires minimum 24 consecutive hours, except day care.",
    },
}


def normalize(text: str) -> str:
    """Normalize text for easier matching."""

    text = text.lower()

    # Normalize currency representations.
    text = text.replace("₹", "rs")
    text = text.replace("rs.", "rs")

    # Remove commas from numbers.
    text = text.replace(",", "")

    return text


def contains_term(text: str, term: str) -> bool:
    """
    Check whether a required term is present.

    Handles cases such as:
    5000
    5,000
    Rs 5,000
    ₹5,000
    """

    text = normalize(text)
    term = normalize(term)

    return term in text


def evaluate_answer(question_id: str, answer: str) -> dict:
    """
    Evaluate one answer using question-specific factual rules.
    """

    if question_id not in CHECKS:
        return {
            "status": "UNKNOWN",
            "reason": "No evaluation rules defined.",
        }

    rules = CHECKS[question_id]

    missing = [
        term
        for term in rules["required"]
        if not contains_term(answer, term)
    ]

    forbidden_found = [
        term
        for term in rules["forbidden"]
        if contains_term(answer, term)
    ]

    # -----------------------------------------------------
    # Determine status
    # -----------------------------------------------------

    if forbidden_found:
        status = "FAIL"

    elif missing:
        status = "PARTIAL"

    else:
        status = "PASS"

    return {
        "status": status,
        "missing_required": missing,
        "forbidden_found": forbidden_found,
        "description": rules["description"],
    }


def main():

    ground_truth_path = Path(
        "data/evaluation/ground_truth.json"
    )

    current_path = Path(
    "data/evaluation/current_results.json"
)

    # -----------------------------------------------------
    # Load files
    # -----------------------------------------------------

    with open(
        ground_truth_path,
        "r",
        encoding="utf-8",
    ) as f:
        ground_truth = json.load(f)

    with open(
    current_path,
    "r",
    encoding="utf-8",
) as f:
        current_results = json.load(f)

    current_by_id = {
    item["id"]: item
    for item in current_results
}

    results = []

    # -----------------------------------------------------
    # Evaluate each question
    # -----------------------------------------------------

    for expected in ground_truth:

        question_id = expected["id"]

        actual_item = current_by_id.get(question_id)

        if not actual_item:
            print(
    f"WARNING: Missing current result for {question_id}"
)
            continue

        answer = actual_item["answer"]

        evaluation = evaluate_answer(
            question_id,
            answer,
        )

        result = {
            "id": question_id,
            **evaluation,
        }

        results.append(result)

    # -----------------------------------------------------
    # Print results
    # -----------------------------------------------------

    print("\n" + "=" * 70)
    print("INSURELENS EVALUATOR V2")
    print("=" * 70)

    passed = 0
    partial = 0
    failed = 0

    for result in results:

        print(
            f"\n{result['id'].upper()} -> "
            f"{result['status']}"
        )

        print(
            f"  Check: {result['description']}"
        )

        if result["missing_required"]:
            print(
                f"  Missing: "
                f"{result['missing_required']}"
            )

        if result["forbidden_found"]:
            print(
                f"  Forbidden found: "
                f"{result['forbidden_found']}"
            )

        if result["status"] == "PASS":
            passed += 1

        elif result["status"] == "PARTIAL":
            partial += 1

        elif result["status"] == "FAIL":
            failed += 1

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    total = len(results)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(f"Total:   {total}")
    print(f"Passed:  {passed}")
    print(f"Partial: {partial}")
    print(f"Failed:  {failed}")

    if total:
        print(
            f"Pass rate: "
            f"{passed / total * 100:.1f}%"
        )


if __name__ == "__main__":
    main()