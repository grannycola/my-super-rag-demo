"""Chunk documents from raw or ingested data."""

from __future__ import annotations

import json
from pathlib import Path

from src.chunking.hierarchical import HierarchicalChunker
from src.chunking.models import DocumentChunk
from src.config import Config, get_config
from src.loaders.base import LoadedDocument
from src.loaders.url_manifest import load_manifest, resolve_source_url
from src.preprocessing.cleaner import DocumentCleaner
from src.preprocessing.normalizer import DocumentNormalizer


def chunk_documents(
    raw_paths: list[Path] | None = None,
    config: Config | None = None,
) -> list[dict]:
    """Load raw documents and split into chunks with metadata."""
    config = config or get_config()
    chunks_path = config.processed_data_dir / "chunks" / "chunks.jsonl"

    if chunks_path.exists() and raw_paths is None:
        return _load_chunks_from_disk(chunks_path)

    documents = _load_raw_documents(raw_paths or [], config)
    cleaner = DocumentCleaner()
    normalizer = DocumentNormalizer()
    documents = normalizer.normalize(cleaner.clean(documents))

    chunker = HierarchicalChunker()
    chunks = chunker.chunk(documents)

    chunks_path.parent.mkdir(parents=True, exist_ok=True)
    with chunks_path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")

    return [chunk.to_dict() for chunk in chunks]


def _load_chunks_from_disk(path: Path) -> list[dict]:
    chunks: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            chunks.append(json.loads(line))
    return chunks


def _load_raw_documents(raw_paths: list[Path], config: Config) -> list[LoadedDocument]:
    if not raw_paths:
        raw_dir = config.raw_data_dir / "langchain"
        raw_paths = list(raw_dir.glob("*.md"))

    documents: list[LoadedDocument] = []
    manifest = load_manifest(config)

    for path in raw_paths:
        content = path.read_text(encoding="utf-8")
        title = path.stem.replace("-", " ").title()
        source_url = manifest.get(path.name)
        if not source_url:
            source_url = resolve_source_url(f"file://{path}", filename=path.name, config=config)
        documents.append(
            LoadedDocument(
                source_url=source_url,
                title=title,
                content=content,
                doc_type="markdown",
                raw_path=path,
            )
        )
    return documents
