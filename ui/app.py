import os
import httpx
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://api:8000").rstrip("/")

st.set_page_config(page_title="NotebookLM-Clone (Gen 1)", layout="wide")
st.title("📚 NotebookLM-Clone (Gen 1)")
st.caption("Step 4: Embed chunks locally → index in Qdrant")

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
    st.subheader("Upload document (Ingest + Chunk + Embed + Index)")

    uploaded = st.file_uploader("PDF / TXT / MD", type=["pdf", "txt", "md"])
    if uploaded is not None:
        if st.button("⬆️ Ingest"):
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")}
            try:
                with httpx.Client(timeout=180.0) as c:
                    r = c.post(f"{API_BASE}/ingest", files=files)
                if r.status_code >= 400:
                    st.error(f"Ingest failed (HTTP {r.status_code})")
                    st.code(r.text)
                else:
                    st.success("Ingested + Indexed ✅")
                    st.session_state.last_ingest = r.json()
            except Exception as e:
                st.error(str(e))

    if "last_ingest" in st.session_state:
        st.subheader("Last ingest result")
        st.json(st.session_state.last_ingest)
    st.divider()
    st.subheader("Retrieval test (Step 5)")

    q = st.text_area("Ask a question (retrieval only)", height=80, placeholder="e.g., What is the refund policy?")
    top_k = st.slider("top_k", 1, 20, 6)
    min_score = st.slider("min_score", 0.0, 1.0, 0.25)

    doc_filter = None
    if st.checkbox("Filter by a specific doc_id"):
        doc_filter = st.text_input("doc_id (paste from Documents list)")

    if st.button("🔎 Retrieve"):
        try:
            payload = {"question": q, "top_k": int(top_k), "min_score": float(min_score)}
            if doc_filter:
                payload["doc_id"] = doc_filter.strip()

            with httpx.Client(timeout=30.0) as c:
                r = c.post(f"{API_BASE}/retrieve", json=payload)

            if r.status_code != 200:
                st.error(f"Retrieve failed (HTTP {r.status_code})")
                st.code(r.text)
            else:
                st.success("Retrieved ✅")
                data = r.json()
                st.json(data)

                # Nice readable view
                for i, res in enumerate(data.get("results", []), start=1):
                    st.markdown(
                        f"**#{i} Score={res['score']:.3f} | {res['doc_name']} | Page {res['page_number']} | Chunk {res['chunk_index']}**"
                    )
                    st.code(res["text"][:1200])
        except Exception as e:
            st.error(str(e))

    st.divider()
    st.subheader("Qdrant debug")
    if st.button("List Qdrant collections"):
        try:
            with httpx.Client(timeout=10.0) as c:
                r = c.get(f"{API_BASE}/qdrant/collections")
            if r.status_code == 200:
                st.json(r.json())
            else:
                st.error(f"Failed (HTTP {r.status_code})")
                st.code(r.text)
        except Exception as e:
            st.error(str(e))

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
        documents = docs_payload.get("documents", [])
        st.write(f"Count: {docs_payload['count']}")
        st.json(docs_payload)

        st.divider()
        st.subheader("Inspect chunks (debug)")

        if documents:
            label_to_id = {
                f"{d['name']} | pages={d['page_count']} | chunks={d['chunk_count']} | {d['id'][:8]}…": d["id"]
                for d in documents
            }
            selected_label = st.selectbox("Select doc", list(label_to_id.keys()), key="chunks_doc")
            doc_id = label_to_id[selected_label]

            limit = st.slider("Limit", 5, 200, 20)
            page_filter = st.number_input("Page filter (0 = all)", min_value=0, value=0, step=1)

            params = {"limit": limit}
            if page_filter and page_filter > 0:
                params["page"] = int(page_filter)

            try:
                with httpx.Client(timeout=10.0) as c:
                    cr = c.get(f"{API_BASE}/documents/{doc_id}/chunks", params=params)
                if cr.status_code == 200:
                    chunks_payload = cr.json()
                    st.write(f"Returned chunks: {chunks_payload['count']}")
                    for ch in chunks_payload["chunks"]:
                        st.markdown(
                            f"**Page {ch['page_number']} | Chunk {ch['chunk_index']} | "
                            f"{ch['start_char']}-{ch['end_char']}**"
                        )
                        st.code(ch["text"][:1200])
                else:
                    st.error(f"Chunk list failed (HTTP {cr.status_code})")
                    st.code(cr.text)
            except Exception as e:
                st.error(str(e))
        else:
            st.info("No documents yet.")

        st.divider()
        st.subheader("Delete a document (SQLite + Qdrant)")

        if not documents:
            st.info("No documents to delete.")
        else:
            options = {
                f"{d['name']}  | pages={d['page_count']} | chunks={d['chunk_count']} | {d['id'][:8]}…": d["id"]
                for d in documents
            }
            selected_label = st.selectbox("Select document", list(options.keys()), key="delete_doc")
            selected_id = options[selected_label]

            confirm = st.checkbox("I understand this will permanently delete the document and its vectors.")
            if st.button("🗑️ Delete selected", disabled=not confirm):
                try:
                    with httpx.Client(timeout=20.0) as c:
                        dr = c.delete(f"{API_BASE}/documents/{selected_id}")
                    if dr.status_code == 200:
                        st.success("Deleted ✅")
                        st.rerun()
                    else:
                        st.error(f"Delete failed (HTTP {dr.status_code})")
                        st.code(dr.text)
                except Exception as e:
                    st.error(str(e))

st.divider()
st.subheader("Next up")
st.write(
    "- Step 5: /retrieve endpoint (embed query → Qdrant search → return chunks+scores)\n"
    "- Step 6: /chat endpoint with strict citations + abstention gate + model mode switch\n"
)
