from app.services.policy_explainer import PolicyExplainer


def main():

    question = "What is the ICU and ICCU room charge limit?"

    print("\n" + "=" * 70)
    print("INSURELENS POLICY EXPLAINER")
    print("=" * 70)

    print(f"\nQuestion: {question}")

    explainer = PolicyExplainer()

    result = explainer.ask(question)

    print("\n" + "-" * 70)
    print("ANSWER")
    print("-" * 70)

    print(result["answer"])

    print("\n" + "-" * 70)
    print("VERIFIED SOURCES")
    print("-" * 70)

    for source in result["sources"]:
        print(
            f"Page {source['page']} — "
            f"{source['section']}"
        )

    print("\n" + "-" * 70)
    print("VERIFICATION")
    print("-" * 70)

    print(result["verification"])


if __name__ == "__main__":
    main()