"""Tests for section-aware chunking."""

from src.chunking.section_aware import SectionAwareChunker
from src.loaders.base import LoadedDocument


def test_section_aware_chunking_preserves_code_blocks():
    content = """# Getting Started

Some intro text.

```python
def hello():
    return "world"
```

More text here.
"""
    doc = LoadedDocument(
        source_url="https://example.com/doc.md",
        title="Test Doc",
        content=content,
        doc_type="markdown",
    )

    chunker = SectionAwareChunker()
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 1
    combined = " ".join(c.text for c in chunks)
    assert "def hello()" in combined
    assert chunks[0].source_url == doc.source_url
    assert chunks[0].heading_path == ["Getting Started"]
