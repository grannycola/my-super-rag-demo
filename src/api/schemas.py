"""Pydantic schemas for API requests and responses."""

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    source: str = Field(default="langchain", description="langchain | urls")
    urls: list[str] | None = None


class IngestResponse(BaseModel):
    documents_loaded: int
    chunks_indexed: int
    message: str


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = None
    rerank: bool = True


class Citation(BaseModel):
    citation_id: str
    source_url: str
    title: str
    section: str
    chunk_id: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    refused: bool
    chunks_used: int


class RetrieveRequest(BaseModel):
    question: str
    top_k: int | None = None
    rerank: bool = True


class RetrievedChunk(BaseModel):
    rank: int
    chunk_id: str
    title: str
    source_url: str
    section: str
    score: float | None = None
    rerank_score: float | None = None
    snippet: str
    text: str


class RetrieveResponse(BaseModel):
    question: str
    chunks: list[RetrievedChunk]
    total: int


class GenerateRequest(BaseModel):
    question: str
    chunks: list[RetrievedChunk]


class GenerateResponse(BaseModel):
    answer: str
    citations: list[Citation]
    refused: bool
    chunks_used: int


class EvaluateResponse(BaseModel):
    total_questions: int
    retrieval_recall: float | None
    keyword_pass_rate: float | None
    report_path: str | None


class HealthResponse(BaseModel):
    status: str
    vector_store: str
    indexed_chunks: int
