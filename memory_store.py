"""Local RAG-backed memory store using ChromaDB.

Embeddings are produced by Chroma's default embedding function
(all-MiniLM-L6-v2 via ONNX), so no API key is required.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import chromadb
from chromadb.config import Settings


DEFAULT_PATH = Path(os.environ.get("MCP_MEMORY_PATH", "./data/chroma")).resolve()
COLLECTION_NAME = os.environ.get("MCP_MEMORY_COLLECTION", "personal_memory")


class MemoryStore:
    """Thin RAG wrapper over a Chroma collection."""

    def __init__(self, path: Path | None = None, collection: str | None = None) -> None:
        self.path = path or DEFAULT_PATH
        self.path.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection or COLLECTION_NAME

        self.client = chromadb.PersistentClient(
            path=str(self.path),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "hnsw:space": "cosine",
                "description": "Personal memories for the MCP demo",
            },
        )

    def add(self, content: str, tags: list[str], source: str | None) -> str:
        memory_id = uuid.uuid4().hex
        metadata = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tags": ",".join(tags),
            "source": source or "",
        }
        self.collection.add(
            ids=[memory_id],
            documents=[content],
            metadatas=[metadata],
        )
        return memory_id

    def search(self, query: str, limit: int, tags: list[str] | None) -> list[dict]:
        fetch_limit = min(limit * 5, 100) if tags else limit
        result = self.collection.query(query_texts=[query], n_results=fetch_limit)
        memories = _flatten_query(result)
        if tags:
            wanted = set(tags)
            memories = [m for m in memories if wanted.intersection(m["tags"])]
        return memories[:limit]

    def list_recent(self, limit: int) -> list[dict]:
        memories = _flatten_get(self.collection.get())
        memories.sort(key=lambda m: m["created_at"], reverse=True)
        return memories[:limit]

    def delete(self, memory_id: str) -> bool:
        existing = self.collection.get(ids=[memory_id])
        if not existing["ids"]:
            return False
        self.collection.delete(ids=[memory_id])
        return True

    def stats(self) -> dict:
        return {
            "count": self.collection.count(),
            "path": str(self.path),
            "collection": self.collection_name,
        }


def _flatten_query(result: dict) -> list[dict]:
    ids = result.get("ids", [[]])[0]
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    return [
        {
            "id": id_,
            "content": doc,
            "created_at": (meta or {}).get("created_at", ""),
            "tags": [t for t in (meta or {}).get("tags", "").split(",") if t],
            "source": (meta or {}).get("source") or None,
            "score": round(1.0 - dist, 4) if dist is not None else None,
        }
        for id_, doc, meta, dist in zip(ids, docs, metas, distances)
    ]


def _flatten_get(result: dict) -> list[dict]:
    ids = result.get("ids", [])
    docs = result.get("documents", [])
    metas = result.get("metadatas", [])
    return [
        {
            "id": id_,
            "content": doc,
            "created_at": (meta or {}).get("created_at", ""),
            "tags": [t for t in (meta or {}).get("tags", "").split(",") if t],
            "source": (meta or {}).get("source") or None,
        }
        for id_, doc, meta in zip(ids, docs, metas)
    ]
