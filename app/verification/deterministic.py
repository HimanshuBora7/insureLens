
import re


POLICY_CONSTRAINTS = {
    "room_rent": {
        "required": ["2%", "5000"],
        "forbidden": ["24 hours", "24 consecutive hours"],
    },

    "icu_iccu": {
        "required": ["5%", "10000"],
        "forbidden": ["2%", "24 hours", "24 consecutive hours"],
    },

    "cataract": {
        "required": ["25%", "40000"],
    },

    "pre_hospitalisation": {
        "required": ["30"],
    },

    "post_hospitalisation": {
        "required": ["60"],
    },

    "pre_existing_disease": {
        "required": ["36"],
    },

    "copayment": {
        "required": ["5%"],
    },

    "hospitalisation": {
        "required": ["24"],
    },
}


def normalize(text: str) -> str:
    """
    Normalize text so numerical comparisons are easier.
    """

    text = text.lower()

    text = text.replace("₹", "rs")
    text = text.replace(",", "")
    text = text.replace("rs.", "rs")

    return text


def contains(text: str, term: str) -> bool:
    """
    Check whether a normalized term exists in text.
    """

    return normalize(term) in normalize(text)


def extract_numbers(text: str) -> set[str]:
    """
    Extract numerical values from text.
    """

    normalized = normalize(text)

    numbers = set(
        re.findall(
            r"\d+(?:\.\d+)?",
            normalized,
        )
    )

    return numbers


def find_rule(question: str) -> str | None:
    """
    Identify which deterministic policy rule applies
    to the user's question.
    """

    q = question.lower()

    if "room rent" in q:
        return "room_rent"

    if "icu" in q or "iccu" in q:
        return "icu_iccu"

    if "cataract" in q:
        return "cataract"

    if "pre-hospitalisation" in q:
        return "pre_hospitalisation"

    if "post-hospitalisation" in q:
        return "post_hospitalisation"

    if "pre-existing" in q:
        return "pre_existing_disease"

    if "co-payment" in q or "copayment" in q:
        return "copayment"

    if "minimum" in q and "hospital" in q:
        return "hospitalisation"

    return None


def deterministic_check(
    question: str,
    answer: str,
) -> dict:

    # -------------------------------------------------
    # STEP 1: Identify applicable policy rule
    # -------------------------------------------------

    rule_name = find_rule(question)

    if rule_name is None:

        return {
            "checked": False,
            "passed": True,
            "missing": [],
            "forbidden_found": [],
            "invented_numbers": [],
            "rule": None,
            "reason": (
                "No deterministic rule defined "
                "for this question."
            ),
        }

    rule = POLICY_CONSTRAINTS[rule_name]

    # -------------------------------------------------
    # STEP 2: Check required policy constraints
    # -------------------------------------------------

    missing = [
        term
        for term in rule["required"]
        if not contains(answer, term)
    ]

    forbidden_found = [
        term
        for term in rule.get("forbidden", [])
        if contains(answer, term)
    ]

    # -------------------------------------------------
    # STEP 3: Detect unsupported Sum Insured examples
    # -------------------------------------------------

    answer_normalized = normalize(answer)

    invented_numbers = []

    sum_insured_pattern = (
        r"(?:sum insured|si)"
        r".{0,40}?"
        r"(?:rs|₹)\s*"
        r"(\d+(?:\.\d+)?)"
    )

    matches = re.findall(
        sum_insured_pattern,
        answer_normalized,
    )

    # Known policy values for the current deterministic rule.
    known_numbers = set()

    for term in rule["required"]:
        known_numbers.update(
            extract_numbers(term)
        )

    for term in rule.get("forbidden", []):
        known_numbers.update(
            extract_numbers(term)
        )

    for number in matches:

        if number not in known_numbers:
            invented_numbers.append(number)

    # -------------------------------------------------
    # STEP 4: Determine final result
    # -------------------------------------------------

    passed = (
        len(missing) == 0
        and len(forbidden_found) == 0
        and len(invented_numbers) == 0
    )

    if passed:

        reason = (
            "All required constraints are present and "
            "no unsupported condition or Sum Insured "
            "example value was detected."
        )

    else:

        reason = (
            "The answer violates one or more deterministic "
            "policy constraints."
        )

    return {
        "checked": True,
        "passed": passed,
        "missing": missing,
        "forbidden_found": forbidden_found,
        "invented_numbers": invented_numbers,
        "rule": rule_name,
        "reason": reason,
    }
