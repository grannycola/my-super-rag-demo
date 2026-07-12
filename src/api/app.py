"""FastAPI routes: /ingest, /query, /evaluate, /health."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from src import chunk, embed, evaluate, generate, ingest
from src.api.schemas import (
    EvaluateResponse,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    RetrieveRequest,
    RetrieveResponse,
    RetrievedChunk,
)
from src.config import get_config
from src.loaders.url_manifest import resolve_source_url
from src.vectorstore.factory import create_vector_store


def create_app() -> FastAPI:
    app = FastAPI(
        title="DocsRAG Lab",
        description="Production-style RAG for technical documentation",
        version="0.1.0",
    )

    def _chunk_to_retrieved(rank: int, chunk: dict) -> RetrievedChunk:
        text = chunk.get("text", "")
        snippet = text[:220] + ("…" if len(text) > 220 else "")
        source_url = resolve_source_url(chunk.get("source_url", ""))
        return RetrievedChunk(
            rank=rank,
            chunk_id=chunk.get("chunk_id", ""),
            title=chunk.get("title", ""),
            source_url=source_url,
            section=chunk.get("section", ""),
            score=chunk.get("score"),
            rerank_score=chunk.get("rerank_score"),
            snippet=snippet,
            text=text,
        )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        config = get_config()
        try:
            store = create_vector_store(config)
            count = store.count()
        except Exception:
            count = 0

        return HealthResponse(
            status="ok",
            vector_store=config.vector_store,
            indexed_chunks=count,
        )

    @app.post("/ingest", response_model=IngestResponse)
    def ingest_docs(request: IngestRequest) -> IngestResponse:
        try:
            paths = ingest.ingest(urls=request.urls, source=request.source)
            chunks = chunk.chunk_documents()
            indexed = embed.embed_and_store(chunks)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return IngestResponse(
            documents_loaded=len(paths),
            chunks_indexed=indexed,
            message="Ingestion pipeline completed",
        )

    @app.post("/retrieve", response_model=RetrieveResponse)
    def retrieve_docs(request: RetrieveRequest) -> RetrieveResponse:
        try:
            from src.retrieve import retrieve

            chunks = retrieve(
                request.question,
                top_k=request.top_k,
                rerank=request.rerank,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        retrieved = [_chunk_to_retrieved(i, c) for i, c in enumerate(chunks, start=1)]
        return RetrieveResponse(
            question=request.question,
            chunks=retrieved,
            total=len(retrieved),
        )

    @app.post("/generate", response_model=GenerateResponse)
    def generate_docs(request: GenerateRequest) -> GenerateResponse:
        try:
            chunks = [chunk.model_dump() for chunk in request.chunks]
            result = generate.generate_answer(request.question, chunks)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return GenerateResponse(
            answer=result["answer"],
            citations=[
                {**c, "source_url": resolve_source_url(c.get("source_url", ""))}
                for c in result.get("citations", [])
            ],
            refused=result.get("refused", False),
            chunks_used=len(result.get("context_chunks", chunks)),
        )

    @app.post("/query", response_model=QueryResponse)
    def query_docs(request: QueryRequest) -> QueryResponse:
        try:
            from src.retrieve import retrieve

            chunks = retrieve(request.question, top_k=request.top_k, rerank=request.rerank)
            result = generate.generate_answer(request.question, chunks)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return QueryResponse(
            answer=result["answer"],
            citations=[
                {**c, "source_url": resolve_source_url(c.get("source_url", ""))}
                for c in result.get("citations", [])
            ],
            refused=result.get("refused", False),
            chunks_used=len(result.get("context_chunks", chunks)),
        )

    @app.post("/evaluate", response_model=EvaluateResponse)
    def run_evaluation() -> EvaluateResponse:
        try:
            report = evaluate.evaluate()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        report_path = None
        config = get_config()
        reports = sorted(config.reports_dir.glob("eval_*.json"))
        if reports:
            report_path = str(reports[-1])

        return EvaluateResponse(
            total_questions=report["total_questions"],
            retrieval_recall=report.get("retrieval_recall"),
            keyword_pass_rate=report.get("keyword_pass_rate"),
            report_path=report_path,
        )

    return app


app = create_app()
