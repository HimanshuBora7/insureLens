from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.llm.ollama_client import OllamaClient
from app.rag.embeddings import EmbeddingModel
from app.rag.retriever import PolicyRetriever
from app.rag.vector_store import VectorStore
from app.runtime import runtime
from app.services.policy_explainer import PolicyExplainer
from app.services.policy_indexer import PolicyIndexer
from app.services.policy_intelligence import PolicyIntelligence
from app.verification.verifier import PolicyVerifier


@asynccontextmanager
async def lifespan(app: FastAPI):
    embedding_model = EmbeddingModel()
    vector_store = VectorStore()
    llm = OllamaClient()

    runtime.indexer = PolicyIndexer(
        embedding_model=embedding_model,
        vector_store=vector_store,
    )
    retriever = PolicyRetriever(
        embedding_model=embedding_model,
        vector_store=vector_store,
    )

    runtime.explainer = PolicyExplainer(
        retriever=retriever,
        llm=llm,
        verifier=PolicyVerifier(client=llm),
    )
    runtime.intelligence = PolicyIntelligence(
        retriever=retriever,
        llm=llm,
    )

    yield

    runtime.indexer = None
    runtime.explainer = None
    runtime.intelligence = None


app = FastAPI(
    title="InsureLens",
    description="Private, evidence-grounded insurance policy understanding.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
