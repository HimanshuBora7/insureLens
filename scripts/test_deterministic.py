
from app.verification.deterministic import deterministic_check


def run_test(name: str, question: str, answer: str):
    result = deterministic_check(
        question=question,
        answer=answer,
    )

    print("\n" + "-" * 70)
    print(name)
    print("-" * 70)

    print("Question:")
    print(question)

    print("\nAnswer:")
    print(answer)

    print("\nResult:")
    print(result)


def main():

    # -------------------------------------------------
    # TEST 1
    # Correct ICU answer
    # -------------------------------------------------

    run_test(
        "TEST 1 — Correct ICU Answer",

        "What is the ICU and ICCU room charge limit?",

        (
            "ICU and ICCU charges are up to 5% of the "
            "Sum Insured subject to a maximum of "
            "Rs 10,000 per day."
        ),
    )

    # -------------------------------------------------
    # TEST 2
    # Incorrect ICU answer containing 2%
    # -------------------------------------------------

    run_test(
        "TEST 2 — Incorrect ICU Percentage",

        "What is the ICU and ICCU room charge limit?",

        (
            "ICU and ICCU charges are limited to 2% "
            "of the Sum Insured with a maximum of "
            "Rs 10,000 per day."
        ),
    )

    # -------------------------------------------------
    # TEST 3
    # Invented Sum Insured example
    # -------------------------------------------------

    run_test(
        "TEST 3 — Invented Sum Insured Example",

        "What is the ICU and ICCU room charge limit?",

        (
            "ICU and ICCU charges are up to 5% of the "
            "Sum Insured subject to a maximum of "
            "Rs 10,000 per day. "
            "For example, if the Sum Insured is "
            "Rs 2,000,000, the limit would be "
            "Rs 100,000 per day."
        ),
    )

    # -------------------------------------------------
    # TEST 4
    # Correct PED waiting period
    # -------------------------------------------------

    run_test(
        "TEST 4 — PED Waiting Period",

        "What is the waiting period for pre-existing diseases?",

        "The waiting period for pre-existing diseases is 36 months.",
    )

    # -------------------------------------------------
    # TEST 5
    # Correct hospitalisation period
    # -------------------------------------------------

    run_test(
        "TEST 5 — Hospitalisation Period",

        (
            "What is the minimum hospitalisation period "
            "for admissible hospitalisation expenses?"
        ),

        (
            "Hospitalisation expenses require a minimum "
            "of 24 consecutive hours, except for Day Care Treatment."
        ),
    )
    #test 6
    run_test( "TEST 6 — Room Rent With Unrelated Hospitalisation Condition", "What is the room rent limit?", ( "Room rent is limited to 2% of the Sum Insured " "subject to a maximum of Rs 5,000 per day. " "The policy also requires a minimum hospitalisation " "period of 24 consecutive hours." ), )

if __name__ == "__main__":
    main()
