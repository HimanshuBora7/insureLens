import os

import requests
import streamlit as st

API_URL = os.getenv("INSURELENS_API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="InsureLens — Understand My Policy",
    page_icon="🔎",
    layout="centered",
)


def init_state() -> None:
    defaults = {
        "document_id": None,
        "filename": None,
        "pages": None,
        "chunks": None,
        "result": None,
        "briefing_result": None,
        "privacy": None,
        "api_error": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def fetch_health() -> dict | None:
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def render_privacy_strip(privacy: dict | None, health: dict | None) -> None:
    if privacy is None and health is not None:
        privacy = health.get("privacy")

    if privacy is None:
        privacy = {
            "privacy_mode": True,
            "local_llm": "Ollama",
            "local_model": "qwen2.5-coder:7b",
            "documents_processed_locally": True,
            "external_verification": False,
        }

    ollama_ok = bool(health and health.get("ollama_reachable"))
    api_ok = health is not None

    st.markdown(
        f"""
<div style="
    border: 1px solid #1f6f4a;
    background: #eef8f2;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 1.2rem;
">
  <strong>🔒 Privacy Mode: ON</strong><br/>
  Local LLM: {privacy.get("local_llm", "Ollama")}
  ({privacy.get("local_model", "local")})
  · Documents processed locally
  · External verification: Off
  <br/>
  <span style="font-size: 0.9rem; color: #335;">
    API: {"connected" if api_ok else "offline"}
    · Ollama: {"reachable" if ollama_ok else "not reachable"}
  </span>
</div>
""",
        unsafe_allow_html=True,
    )


def format_source_line(source: dict, filename: str) -> str:
    document = source.get("document") or filename
    page = source.get("page")
    section = source.get("section", "Unknown Section")
    return f"📄 Source: {document} — Page {page}, {section}"


def render_briefing_items(items: list[dict], filename: str, concern: bool = False) -> None:
    if not items:
        st.caption("No supported items found in the retrieved clauses.")
        return

    for item in items:
        st.markdown(f"**{item.get('label', 'Clause')}**")
        st.write(item.get("detail", ""))

        if concern and item.get("why_it_matters"):
            st.write(item["why_it_matters"])

        for source in item.get("sources") or []:
            st.caption(format_source_line(source, filename))


def render_briefing(result: dict) -> None:
    briefing = result.get("briefing") or {}
    filename = result.get("filename") or "Policy.pdf"

    st.subheader("Coverage")
    render_briefing_items(briefing.get("coverage") or [], filename)

    st.subheader("⚠️ Important clauses")
    render_briefing_items(briefing.get("important_clauses") or [], filename)

    st.subheader("🚨 Potential concerns")
    render_briefing_items(
        briefing.get("potential_concerns") or [],
        filename,
        concern=True,
    )

    with st.expander("Waiting periods"):
        render_briefing_items(briefing.get("waiting_periods") or [], filename)

    with st.expander("Co-payment"):
        render_briefing_items(briefing.get("copayment") or [], filename)

    with st.expander("Deductibles"):
        render_briefing_items(briefing.get("deductibles") or [], filename)

    with st.expander("Sub-limits"):
        render_briefing_items(briefing.get("sub_limits") or [], filename)

    with st.expander("Exclusions"):
        render_briefing_items(briefing.get("exclusions") or [], filename)

    st.subheader("Verification")
    render_verification(result.get("verification") or {})


def render_verification(verification: dict) -> None:
    action = str(verification.get("action", "REVIEW")).upper()
    grounded = bool(verification.get("grounded"))
    confidence = verification.get("confidence", 0.0)

    if action == "ACCEPT" and grounded:
        st.success(
            f"Verification: {action} · grounded · confidence {confidence:.2f}"
        )
    elif action == "REGENERATE":
        st.error(
            f"Verification: {action} · not grounded · confidence {confidence:.2f}"
        )
    else:
        st.warning(
            f"Verification: {action} · confidence {confidence:.2f}"
        )

    unsupported = verification.get("unsupported_claims") or []

    if unsupported:
        with st.expander("Unsupported claims"):
            for claim in unsupported:
                st.write(f"- {claim}")


init_state()

st.title("InsureLens")
st.caption(
    "Private, evidence-grounded AI for insurance understanding."
)

health = fetch_health()
privacy = st.session_state.privacy or (
    health.get("privacy") if health else None
)
render_privacy_strip(privacy, health)

st.header("Understand My Policy")
st.write(
    "Upload a policy PDF, ask a question, and get an answer "
    "with page-level citations. Documents stay on this machine."
)

if health is None:
    st.error(
        f"Cannot reach the InsureLens API at `{API_URL}`. "
        "Start it with `uvicorn app.main:app --reload --port 8000`."
    )

uploaded = st.file_uploader(
    "Upload an insurance policy (PDF)",
    type=["pdf"],
)

if uploaded is not None and st.button("Index this policy", type="primary"):
    with st.spinner("Indexing locally: extract → chunk → embed → store..."):
        try:
            response = requests.post(
                f"{API_URL}/upload",
                files={
                    "file": (
                        uploaded.name,
                        uploaded.getvalue(),
                        "application/pdf",
                    )
                },
                timeout=300,
            )

            if response.status_code >= 400:
                try:
                    detail = response.json().get("detail", response.text)
                except ValueError:
                    detail = response.text
                st.session_state.api_error = str(detail)
            else:
                payload = response.json()
                st.session_state.document_id = payload["document_id"]
                st.session_state.filename = payload["filename"]
                st.session_state.pages = payload["pages"]
                st.session_state.chunks = payload["chunks"]
                st.session_state.privacy = payload.get("privacy")
                st.session_state.result = None
                st.session_state.briefing_result = None
                st.session_state.api_error = None
        except requests.RequestException as exc:
            st.session_state.api_error = str(exc)

if st.session_state.api_error:
    st.error(st.session_state.api_error)

if st.session_state.document_id:
    st.info(
        f"Indexed **{st.session_state.filename}** · "
        f"{st.session_state.pages} pages · "
        f"{st.session_state.chunks} chunks"
    )

    question = st.text_area(
        "Ask a question about this policy",
        placeholder=(
            "What are the things I should be careful about in this policy?"
        ),
        height=100,
    )

    ask_col, review_col = st.columns(2)

    with ask_col:
        ask_clicked = st.button("Ask", type="primary")

    with review_col:
        review_clicked = st.button("What should I be careful about?")

    if review_clicked:
        with st.spinner(
            "Retrieving coverage, exclusions, waiting periods, and limits..."
        ):
            try:
                response = requests.post(
                    f"{API_URL}/analyze",
                    json={"document_id": st.session_state.document_id},
                    timeout=240,
                )

                if response.status_code >= 400:
                    try:
                        detail = response.json().get("detail", response.text)
                    except ValueError:
                        detail = response.text
                    st.session_state.api_error = str(detail)
                    st.session_state.result = None
                else:
                    st.session_state.result = response.json()
                    st.session_state.privacy = (
                        st.session_state.result.get("privacy")
                    )
                    st.session_state.api_error = None
            except requests.RequestException as exc:
                st.session_state.api_error = str(exc)

    elif ask_clicked:
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            with st.spinner("Retrieving clauses and asking the local model..."):
                try:
                    response = requests.post(
                        f"{API_URL}/ask",
                        json={
                            "document_id": st.session_state.document_id,
                            "question": question.strip(),
                        },
                        timeout=240,
                    )

                    if response.status_code >= 400:
                        try:
                            detail = response.json().get("detail", response.text)
                        except ValueError:
                            detail = response.text
                        st.session_state.api_error = str(detail)
                        st.session_state.result = None
                    else:
                        st.session_state.result = response.json()
                        st.session_state.privacy = (
                            st.session_state.result.get("privacy")
                        )
                        st.session_state.api_error = None
                except requests.RequestException as exc:
                    st.session_state.api_error = str(exc)

result = st.session_state.result

if result and result.get("briefing"):
    render_briefing(result)
elif result:
    st.subheader("Answer")
    st.markdown(result.get("answer") or "")

    st.subheader("Evidence")
    sources = result.get("sources") or []
    filename = result.get("filename") or "Policy.pdf"

    if not sources:
        st.write("No citations were attached.")
    else:
        for source in sources:
            st.markdown(f"- **{format_source_line(source, filename)}**")

    st.subheader("Verification")
    render_verification(result.get("verification") or {})
