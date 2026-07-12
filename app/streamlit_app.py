"""Streamlit demo UI for DocsRAG Lab."""

import streamlit as st

from src.generate import generate_answer
from src.retrieve import retrieve

st.set_page_config(page_title="DocsRAG Lab", page_icon="📚", layout="wide")

st.title("DocsRAG Lab")
st.caption("Ask questions about LangChain documentation")

query = st.text_input("Your question")

if st.button("Ask") and query:
    with st.spinner("Searching documentation..."):
        try:
            chunks = retrieve(query)
            result = generate_answer(query, chunks)

            st.markdown(result["answer"])

            if result.get("citations"):
                st.subheader("Sources")
                for cite in result["citations"]:
                    st.markdown(f"- {cite['citation_id']} [{cite['title']}]({cite['source_url']})")
        except Exception as exc:
            st.error(f"Error: {exc}")
