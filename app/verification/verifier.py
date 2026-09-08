import json

from app.llm.ollama_client import OllamaClient
from app.verification.deterministic import deterministic_check


class PolicyVerifier:

    def __init__(self, client: OllamaClient | None = None):
        self.client = client or OllamaClient()

    def verify(
        self,
        question: str,
        answer: str,
        retrieved_chunks: list[dict],
    ) -> dict:

        # -------------------------------------------------
        # STEP 1: Deterministic verification
        # -------------------------------------------------

        deterministic_result = deterministic_check(
            question=question,
            answer=answer,
        )

        # -------------------------------------------------
        # STEP 2: LLM semantic verification
        # -------------------------------------------------

        context_parts = []

        for i, chunk in enumerate(retrieved_chunks, start=1):

            context_parts.append(
                f"""
SOURCE {i}
PAGE: {chunk['page']}
SECTION: {chunk.get('section', 'Unknown Section')}

{chunk['text']}
"""
            )

        context = "\n".join(context_parts)

        prompt = f"""
You are a strict evidence verification system for InsureLens.

Your task is to check whether each factual claim in the
generated answer is directly supported by the provided
insurance policy evidence.

USER QUESTION:
{question}

GENERATED ANSWER:
{answer}

POLICY EVIDENCE:
{context}

IMPORTANT RULES:

1. Break the generated answer into individual factual claims.

2. Verify EVERY factual claim independently.

3. A claim is SUPPORTED only if the provided evidence directly
   supports the complete meaning of the claim.

4. Do not use outside knowledge.

5. Do not infer relationships between facts merely because
   they appear in the same source or on the same page.

6. Pay special attention to percentages, monetary limits,
   durations, thresholds and exceptions.

7. If a claim combines multiple facts, verify BOTH:
   a) that each fact appears in the evidence, AND
   b) that the evidence explicitly connects those facts.

8. A fact appearing somewhere in the evidence does NOT mean
   it is a condition of another fact.

9. For example, if the evidence says:
      "Room rent is limited to 2% of Sum Insured"
   and separately says:
      "Hospitalisation expenses require 24 hours"
   you MUST NOT conclude:
      "Room rent requires 24 hours"
   unless the evidence explicitly makes that connection.

10. Distinguish between:
    - a condition of a specific benefit,
    - a general policy condition,
    - an exception,
    - and an unrelated statement.

11. If a claim contains an example, verify that the example
    logically follows from the policy rule.

12. Check whether numerical calculations in the answer are
    consistent with the policy.

13. A plausible claim is NOT necessarily a supported claim.

14. Check whether the cited page actually supports the claim.

15. Do not judge whether the policy itself is fair or reasonable.

16. Only judge whether the generated answer is supported
    by the provided evidence.

17. When uncertain about the relationship between two facts,
    mark the claim as UNSUPPORTED rather than assuming the
    relationship.
CONFIDENCE GUIDELINES:

- 0.90-1.00:
  Only when every claim is directly and explicitly supported.

- 0.70-0.89:
  Evidence is mostly supportive but there is some ambiguity.

- 0.40-0.69:
  Important uncertainty or incomplete support exists.

- 0.00-0.39:
  One or more important claims are contradicted or unsupported.

If any important factual claim is unsupported,
do NOT return grounded=true.

If the evidence does not explicitly establish a relationship
between two facts, treat that relationship as unsupported.
Return ONLY valid JSON.

Use exactly this structure:

{{
    "claims": [
        {{
            "claim": "example claim",
            "supported": true,
            "evidence_pages": [32],
            "reason": "The policy explicitly supports this claim."
        }}
    ],
    "grounded": true,
    "citation_supported": true,
    "unsupported_claims": [],
    "confidence": 0.90,
    "action": "ACCEPT"
}}

Possible action values:

ACCEPT
REGENERATE
REVIEW

Do not include markdown.
Do not include explanations outside the JSON.
"""

        response = self.client.generate(prompt).strip()

        # Remove markdown code fences if the model adds them.
        if response.startswith("```"):
            response = response.replace("```json", "")
            response = response.replace("```", "")
            response = response.strip()

        try:
            llm_result = json.loads(response)

        except json.JSONDecodeError:

            llm_result = {
                "claims": [],
                "grounded": False,
                "citation_supported": False,
                "unsupported_claims": [
                    "Verifier returned invalid JSON."
                ],
                "confidence": 0.0,
                "action": "REVIEW",
            }

        # -------------------------------------------------
        # STEP 3: Combine the two verification layers
        # -------------------------------------------------

        if not deterministic_result["passed"]:

            final_action = "REGENERATE"

            final_grounded = False

        elif not llm_result.get("grounded", False):

            final_action = "REVIEW"

            final_grounded = False

        else:

            final_action = llm_result.get(
                "action",
                "REVIEW",
            )

            final_grounded = True

        # -------------------------------------------------
        # STEP 4: Return complete verification result
        # -------------------------------------------------

        return {
            "grounded": final_grounded,

            "citation_supported": llm_result.get(
                "citation_supported",
                False,
            ),

            "confidence": llm_result.get(
                "confidence",
                0.0,
            ),

            "action": final_action,

            "deterministic": deterministic_result,

            "claims": llm_result.get(
                "claims",
                [],
            ),

            "unsupported_claims": llm_result.get(
                "unsupported_claims",
                [],
            ),
        }