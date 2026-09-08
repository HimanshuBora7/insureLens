import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from requests import RequestException

from app.llm.ollama_client import OllamaClient
from app.privacy import privacy_flags
from app.runtime import runtime
from app.services.policy_intelligence import (
    briefing_to_answer,
    is_policy_review_question,
)

router = APIRouter()


class AskRequest(BaseModel):
    document_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)


class AnalyzeRequest(BaseModel):
    document_id: str = Field(min_length=1)


def _privacy() -> dict:
    model = "qwen2.5-coder:7b"

    if runtime.explainer is not None:
        model = runtime.explainer.llm.model

    return privacy_flags(model)


def _require_services() -> None:
    if (
        runtime.indexer is None
        or runtime.explainer is None
        or runtime.intelligence is None
    ):
        raise HTTPException(
            status_code=503,
            detail="InsureLens services are still starting.",
        )


def _with_document_sources(sources: list[dict], filename: str) -> list[dict]:
    labelled = []

    for source in sources:
        labelled.append({**source, "document": filename})

    return labelled


def _analyze_document(document_id: str) -> dict:
    meta = runtime.indexer.get_meta(document_id)

    if meta is None:
        raise HTTPException(
            status_code=404,
            detail="No indexed policy found for this document_id. Upload a PDF first.",
        )

    try:
        result = runtime.intelligence.summarize(document_id=document_id)
    except RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail="Local LLM is unavailable. Is Ollama running?",
        ) from exc

    filename = meta["filename"]
    briefing = result["briefing"]

    for category, items in briefing.items():
        for item in items:
            item["sources"] = _with_document_sources(
                item.get("sources") or [],
                filename,
            )

    return {
        "document_id": document_id,
        "filename": filename,
        "answer": briefing_to_answer(briefing),
        "briefing": briefing,
        "sources": _with_document_sources(result["sources"], filename),
        "verification": result["verification"],
        "privacy": _privacy(),
    }


@router.get("/health")
def health() -> dict:
    ollama_reachable = False
    model = "qwen2.5-coder:7b"

    if runtime.explainer is not None:
        model = runtime.explainer.llm.model
        ollama_reachable = runtime.explainer.llm.is_reachable()
    else:
        ollama_reachable = OllamaClient().is_reachable()

    return {
        "status": "ok",
        "ollama_reachable": ollama_reachable,
        "privacy": privacy_flags(model),
    }


@router.post("/upload")
async def upload_policy(
    file: UploadFile = File(...),
) -> dict:
    _require_services()

    filename = file.filename or "policy.pdf"

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF policy document.",
        )

    file_bytes = await file.read()

    if not file_bytes.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid PDF.",
        )

    document_id = str(uuid.uuid4())

    try:
        meta = runtime.indexer.index_upload(
            file_bytes=file_bytes,
            filename=filename,
            document_id=document_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        **meta,
        "privacy": _privacy(),
    }


@router.post("/analyze")
def analyze_policy(request: AnalyzeRequest) -> dict:
    _require_services()
    return _analyze_document(request.document_id)


@router.post("/ask")
def ask_policy(request: AskRequest) -> dict:
    _require_services()

    if is_policy_review_question(request.question):
        payload = _analyze_document(request.document_id)
        payload["question"] = request.question.strip()
        return payload

    meta = runtime.indexer.get_meta(request.document_id)

    if meta is None:
        raise HTTPException(
            status_code=404,
            detail="No indexed policy found for this document_id. Upload a PDF first.",
        )

    try:
        result = runtime.explainer.ask(
            question=request.question.strip(),
            top_k=request.top_k,
            document_id=request.document_id,
        )
    except RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail="Local LLM is unavailable. Is Ollama running?",
        ) from exc

    filename = meta["filename"]

    for source in result["sources"]:
        source["document"] = filename

    return {
        "document_id": request.document_id,
        "filename": filename,
        "question": request.question.strip(),
        "answer": result["answer"],
        "sources": result["sources"],
        "verification": result["verification"],
        "privacy": _privacy(),
    }
