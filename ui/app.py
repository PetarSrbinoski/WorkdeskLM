import os
import httpx
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://api:8000").rstrip("/")

st.set_page_config(page_title="NotebookLM-Clone (Gen 1)", layout="wide")
st.title("📚 NotebookLM-Clone (Gen 1)")
st.caption("Step 2: Ingest (PDF/TXT/MD) → parse pages → store locally (SQLite)")

left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("Service Status")
    if st.button("🔄 Refresh health"):
        st.session_state.pop("health", None)

    if "health" not in st.session_state:
        try:
            with httpx.Client(timeout=5.0) as c:
                r = c.get(f"{API_BASE}/health")
                st.session_state.health = (r.status_code, r.json())
        except Exception as e:
            st.session_state.health = (None, {"error": str(e)})

    code, data = st.session_state.health
    if code == 200:
        st.success("Healthy ✅")
    elif code is None:
        st.error("UI can't reach API ❌")
    else:
        st.warning(f"Degraded (HTTP {code}) ⚠️")

    st.write("API Base:", API_BASE)

    st.divider()
    st.subheader("Upload document (Step 2)")

    uploaded = st.file_uploader("PDF / TXT / MD", type=["pdf", "txt", "md"])
    if uploaded is not None:
        if st.button("⬆️ Ingest"):
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")}
            try:
                with httpx.Client(timeout=60.0) as c:
                    r = c.post(f"{API_BASE}/ingest", files=files)
                if r.status_code >= 400:
                    st.error(f"Ingest failed (HTTP {r.status_code})")
                    st.code(r.text)
                else:
                    st.success("Ingested ✅")
                    st.session_state.last_ingest = r.json()
            except Exception as e:
                st.error(str(e))

    if "last_ingest" in st.session_state:
        st.subheader("Last ingest result")
        st.json(st.session_state.last_ingest)

with right:
    st.subheader("Documents")
    docs_payload = None
    try:
        with httpx.Client(timeout=5.0) as c:
            r = c.get(f"{API_BASE}/documents")
        if r.status_code == 200:
            docs_payload = r.json()
        else:
            st.error(f"Failed to list documents (HTTP {r.status_code})")
            st.code(r.text)
    except Exception as e:
        st.error(str(e))

    if docs_payload:
        st.write(f"Count: {docs_payload['count']}")
        documents = docs_payload.get("documents", [])

        # Show JSON for transparency (nice for debugging)
        st.json(docs_payload)

        st.divider()
        st.subheader("Delete a document")

        if not documents:
            st.info("No documents to delete.")
        else:
            # Build dropdown label -> doc_id map
            options = {
                f"{d['name']}  | pages={d['page_count']} | {d['id'][:8]}…": d["id"]
                for d in documents
            }
            selected_label = st.selectbox("Select document", list(options.keys()))
            selected_id = options[selected_label]

            confirm = st.checkbox("I understand this will permanently delete the document (SQLite).")
            if st.button("🗑️ Delete selected", disabled=not confirm):
                try:
                    with httpx.Client(timeout=10.0) as c:
                        dr = c.delete(f"{API_BASE}/documents/{selected_id}")
                    if dr.status_code == 200:
                        st.success("Deleted ✅")
                        # refresh view
                        st.session_state.pop("health", None)
                        st.rerun()
                    else:
                        st.error(f"Delete failed (HTTP {dr.status_code})")
                        st.code(dr.text)
                except Exception as e:
                    st.error(str(e))


st.divider()
st.subheader("Next up")
st.write(
    "- Step 3: Chunking with overlap + chunk metadata\n"
    "- Step 4: Embeddings + Qdrant upsert\n"
    "- Step 5: Retrieval endpoint (/retrieve)\n"
    "- Step 6: Chat endpoint (/chat) with strict citations + abstention\n"
)
