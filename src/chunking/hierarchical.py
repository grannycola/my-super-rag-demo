"""Hierarchical chunking with parent-child section relationships."""

from __future__ import annotations

from src.chunking.models import DocumentChunk
from src.chunking.section_aware import SectionAwareChunker
from src.loaders.base import LoadedDocument


class HierarchicalChunker:
    """Split documents into hierarchical chunks preserving heading structure."""

    def __init__(self, section_chunker: SectionAwareChunker | None = None) -> None:
        self.section_chunker = section_chunker or SectionAwareChunker()

    def chunk(self, documents: list[LoadedDocument]) -> list[DocumentChunk]:
        all_chunks: list[DocumentChunk] = []
        for doc in documents:
            section_chunks = self.section_chunker.chunk_document(doc)
            for i, chunk in enumerate(section_chunks):
                chunk.metadata["hierarchy_level"] = len(chunk.heading_path)
                chunk.metadata["chunk_index"] = i
                chunk.metadata["parent_doc_url"] = doc.source_url
                all_chunks.append(chunk)
        return all_chunks
