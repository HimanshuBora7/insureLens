from app.llm.ollama_client import OllamaClient


def main():
    client = OllamaClient()

    prompt = """
You are an insurance policy assistant.

Explain this insurance clause in simple language:

"A 20% co-payment shall apply to all admissible hospitalization expenses."

Give:
1. A simple explanation
2. A numerical example using Indian rupees
3. One important thing the customer should check

Do not give legal advice.
Do not invent policy conditions that are not present in the clause.
"""

    answer = client.generate(prompt)

    print("\n--- InsureLens Response ---\n")
    print(answer)


if __name__ == "__main__":
    main()