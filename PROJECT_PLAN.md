# DocsRAG Lab — Project Plan

## One-line description

Production-style RAG system for technical documentation with automatic ingestion, source citations, evaluation, and experiment tracking.

## Problem

Technical documentation is large, fragmented, and frequently updated. Developers need reliable answers with references to original sources.

## Solution

DocsRAG Lab indexes technical documentation and allows users to ask questions. The system retrieves relevant chunks, generates grounded answers, shows citations, and evaluates answer quality.

## Initial corpus

LangChain documentation.

## MVP

- collect documentation pages
- clean and store raw documents
- split documents into chunks
- generate embeddings
- store chunks in vector DB
- retrieve relevant chunks by query
- generate answer with citations
- log retrieved chunks and answer

## Later improvements

- Airflow ingestion pipeline
- change detection
- RAGAS evaluation
- reranking
- hybrid search
- Streamlit demo
- project landing page
