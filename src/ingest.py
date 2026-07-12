"""Ingest pipeline: loader → parser → cleaner → chunker → metadata enricher."""

from __future__ import annotations

from pathlib import Path

from src.chunking.hierarchical import HierarchicalChunker
from src.config import Config, get_config
from src.loaders.langchain_docs import LangChainDocsLoader
from src.loaders.sitemap import SitemapLoader
from src.loaders.url_manifest import save_manifest
from src.preprocessing.cleaner import DocumentCleaner
from src.preprocessing.normalizer import DocumentNormalizer


def ingest(
    urls: list[str] | None = None,
    source: str = "langchain",
    config: Config | None = None,
) -> list[Path]:
    """
    Full ingestion pipeline:
    docs source → crawler/loader → parser → cleaner → chunker → metadata enricher
    """
    config = config or get_config()

    if source == "langchain":
        loader = LangChainDocsLoader(config)
        documents = loader.load(urls)
    elif urls:
        loader = SitemapLoader(config)
        documents = loader.load(urls)
    else:
        sources_file = config.raw_data_dir / "langchain" / "sources.txt"
        if sources_file.exists():
            loader = SitemapLoader(config)
            documents = loader.load_from_file(sources_file)
        else:
            loader = LangChainDocsLoader(config)
            documents = loader.load()

    cleaner = DocumentCleaner()
    normalizer = DocumentNormalizer()
    documents = normalizer.normalize(cleaner.clean(documents))

    save_manifest(documents, config)

    chunker = HierarchicalChunker()
    chunks = chunker.chunk(documents)

    processed_dir = config.processed_data_dir / "chunks"
    processed_dir.mkdir(parents=True, exist_ok=True)

    import json

    chunks_path = processed_dir / "chunks.jsonl"
    with chunks_path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")

    return [doc.raw_path for doc in documents if doc.raw_path]
