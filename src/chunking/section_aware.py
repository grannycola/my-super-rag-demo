"""Section-aware and code-aware text splitting."""

from __future__ import annotations

import re

from src.chunking.models import DocumentChunk, make_chunk_id
from src.config import Config, get_config
from src.loaders.base import LoadedDocument

CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```", re.MULTILINE)
SECTION_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


class SectionAwareChunker:
    """Split documents by sections, preserving code blocks."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or get_config()

    def chunk_document(self, document: LoadedDocument) -> list[DocumentChunk]:
        sections = self._split_by_sections(document.content)
        chunks: list[DocumentChunk] = []

        for section_idx, (heading_path, section_text) in enumerate(sections):
            sub_chunks = self._split_preserving_code(section_text)
            for sub_idx, text in enumerate(sub_chunks):
                chunk_id = make_chunk_id(document.source_url, section_idx * 100 + sub_idx)
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        text=text,
                        source_url=document.source_url,
                        title=document.title,
                        section=heading_path[-1] if heading_path else document.title,
                        heading_path=heading_path,
                        doc_type=document.doc_type,
                        last_updated=document.last_updated,
                    )
                )

        return chunks

    def _split_by_sections(self, content: str) -> list[tuple[list[str], str]]:
        matches = list(SECTION_PATTERN.finditer(content))
        if not matches:
            return [([], content)]

        sections: list[tuple[list[str], str]] = []
        heading_stack: list[tuple[int, str]] = []

        for i, match in enumerate(matches):
            level = len(match.group(1))
            heading = match.group(2).strip()
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, heading))
            heading_path = [h[1] for h in heading_stack]

            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            section_text = content[start:end].strip()
            if section_text:
                sections.append((heading_path, section_text))

        return sections or [([], content)]

    def _split_preserving_code(self, text: str) -> list[str]:
        if len(text) <= self.config.chunk_size:
            return [text] if text.strip() else []

        chunks: list[str] = []
        protected = text
        placeholders: dict[str, str] = {}

        for i, match in enumerate(CODE_BLOCK_PATTERN.finditer(text)):
            key = f"__CODE_BLOCK_{i}__"
            placeholders[key] = match.group(0)
            protected = protected.replace(match.group(0), key, 1)

        words = protected.split()
        current: list[str] = []
        current_len = 0

        for word in words:
            word_len = len(word) + 1
            if current_len + word_len > self.config.chunk_size and current:
                chunk_text = " ".join(current)
                for key, code in placeholders.items():
                    chunk_text = chunk_text.replace(key, code)
                chunks.append(chunk_text)
                overlap_words = current[-max(1, self.config.chunk_overlap // 10):]
                current = overlap_words + [word]
                current_len = sum(len(w) + 1 for w in current)
            else:
                current.append(word)
                current_len += word_len

        if current:
            chunk_text = " ".join(current)
            for key, code in placeholders.items():
                chunk_text = chunk_text.replace(key, code)
            chunks.append(chunk_text)

        return chunks
