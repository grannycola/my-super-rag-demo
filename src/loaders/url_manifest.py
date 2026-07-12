"""Map local raw filenames to public documentation URLs."""

from __future__ import annotations

import json
import re
from pathlib import Path

import requests

from src.config import Config, get_config

LLMS_TXT_URL = "https://docs.langchain.com/llms.txt"
MANIFEST_NAME = "sources.json"


def manifest_path(config: Config | None = None) -> Path:
    config = config or get_config()
    return config.raw_data_dir / "langchain" / MANIFEST_NAME


def save_manifest(documents: list, config: Config | None = None) -> Path:
    """Save filename → source_url mapping from loaded documents."""
    config = config or get_config()
    mapping: dict[str, str] = {}
    for doc in documents:
        if doc.raw_path and doc.source_url and not doc.source_url.startswith("file://"):
            mapping[doc.raw_path.name] = doc.source_url

    path = manifest_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_manifest(config: Config | None = None) -> dict[str, str]:
    path = manifest_path(config)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def build_manifest_from_llms_txt(config: Config | None = None) -> dict[str, str]:
    """Build filename → URL map from docs.langchain.com llms.txt."""
    config = config or get_config()
    response = requests.get(LLMS_TXT_URL, timeout=30)
    response.raise_for_status()
    urls = re.findall(r"https://docs\.langchain\.com/[^\)\s]+\.md", response.text)

    mapping = {url.rstrip("/").split("/")[-1]: url for url in urls}
    path = manifest_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
    return mapping


def resolve_source_url(
    source_url: str,
    filename: str | None = None,
    config: Config | None = None,
) -> str:
    """Replace local file:// paths with public documentation URLs."""
    if not source_url.startswith("file://"):
        return source_url

    name = filename or Path(source_url.removeprefix("file://")).name
    manifest = load_manifest(config)
    if not manifest:
        try:
            manifest = build_manifest_from_llms_txt(config)
        except Exception:
            return f"https://docs.langchain.com/{Path(name).stem}"

    return manifest.get(name, f"https://docs.langchain.com/{Path(name).stem}")
