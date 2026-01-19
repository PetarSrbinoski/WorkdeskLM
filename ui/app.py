import os
import time
import httpx
import streamlit as st


API_BASE = os.getenv("API_BASE_URL", "http://api:8000").rstrip("/")

st.set_page_config(page_title="NotebookLM-Clone (Gen 1)", layout="wide")

st.title("📚 NotebookLM-Clone (Gen 1)")
st.caption("Step 0–1: Compose infra + /health checks (Qdrant + Ollama)")

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("Service Status")
    refresh = st.button("🔄 Refresh health")

    if "last_health" not in st.session_state:
        st.session_state.last_health = None

    if refresh or st.session_state.last_health is None:
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(f"{API_BASE}/health")
                st.session_state.last_health = (r.status_code, r.json())
        except Exception as e:
            st.session_state.last_health = (None, {"error": str(e)})

    code, data = st.session_state.last_health

    if code == 200:
        st.success("Healthy ✅")
    elif code is None:
        st.error("UI can't reach API ❌")
    else:
        st.warning(f"Degraded (HTTP {code}) ⚠️")

    st.write("API Base:", API_BASE)

with col2:
    st.subheader("Health Payload")
    st.json(data)

st.divider()
st.subheader("Next up")
st.write(
    "- Step 2: /ingest (parse PDF/TXT/MD)\n"
    "- Step 3: chunking\n"
    "- Step 4: embeddings + Qdrant upsert\n"
    "- Step 5: retrieval endpoint\n"
    "- Step 6: /chat with strict citations\n"
)
