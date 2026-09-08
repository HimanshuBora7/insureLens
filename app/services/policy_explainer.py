from app.rag.retriever import PolicyRetriever
from app.rag.prompt_builder import build_policy_prompt
from app.llm.ollama_client import OllamaClient
from app.verification.verifier import PolicyVerifier


class PolicyExplainer:

    def __init__(
        self,
        retriever: PolicyRetriever | None = None,
        llm: OllamaClient | None = None,
        verifier: PolicyVerifier | None = None,
    ):
        self.retriever = retriever or PolicyRetriever()
        self.llm = llm or OllamaClient()
        self.verifier = verifier or PolicyVerifier()

    def ask(
        self,
        question: str,
        top_k: int = 5,
        document_id: str | None = None,
    ) -> dict:

        # Step 1: Retrieve relevant policy evidence
        retrieved_chunks = self.retriever.retrieve(
            query=question,
            top_k=top_k,
            document_id=document_id,
        )

        if not retrieved_chunks:
            return {
                "answer": (
                    "I could not find sufficient evidence "
                    "in the uploaded policy."
                ),
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

        # Step 2: Build grounded prompt
        prompt = build_policy_prompt(
            question=question,
            retrieved_chunks=retrieved_chunks,
        )

        # Step 3: Generate answer using Ollama
        answer = self.llm.generate(prompt)

        # Step 4: Verify generated answer
        verification = self.verifier.verify(
            question=question,
            answer=answer,
            retrieved_chunks=retrieved_chunks,
        )

        # Step 5: Build application-controlled sources
        sources = []
        seen = set()

        for chunk in retrieved_chunks:

            page = chunk["page"]

            section = chunk.get(
                "section",
                "Unknown Section",
            )

            source_key = (page, section)

            if source_key not in seen:

                sources.append(
                    {
                        "page": page,
                        "section": section,
                    }
                )

                seen.add(source_key)

        # Step 6: Return complete result
        return {
            "answer": answer,
            "sources": sources,
            "verification": verification,
        }