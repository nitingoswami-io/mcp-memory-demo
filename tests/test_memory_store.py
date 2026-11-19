"""Tests for the RAG memory store. They run offline after the first run
(Chroma downloads the MiniLM ONNX model once, ~80 MB, into ~/.cache/chroma)."""
from __future__ import annotations

import pytest

from memory_store import MemoryStore


@pytest.fixture()
def store(tmp_path):
    return MemoryStore(path=tmp_path, collection="test_memory")


def test_add_returns_id_and_counts(store):
    memory_id = store.add("I like green tea.", tags=["food"], source="test")
    assert len(memory_id) == 32
    assert store.stats()["count"] == 1


def test_recall_ranks_the_relevant_memory_first(store):
    store.add("Reading list: Designing Data-Intensive Applications.", tags=["books"], source=None)
    store.add("Dentist appointment every six months.", tags=["health"], source=None)
    hits = store.search("what book should I read next?", limit=2, tags=None)
    assert hits[0]["content"].startswith("Reading list")
    assert hits[0]["score"] > hits[1]["score"]


def test_tag_filter_only_returns_matching_memories(store):
    store.add("Project Atlas kicks off on Nov 3.", tags=["work"], source="slack")
    store.add("I prefer dark-roast coffee.", tags=["food"], source=None)
    hits = store.search("coffee", limit=5, tags=["work"])
    assert [h["tags"] for h in hits] == [["work"]]


def test_list_recent_is_newest_first(store):
    store.add("first", tags=[], source=None)
    store.add("second", tags=[], source=None)
    assert [m["content"] for m in store.list_recent(limit=2)] == ["second", "first"]


def test_delete_reports_whether_anything_was_removed(store):
    memory_id = store.add("temporary", tags=[], source=None)
    assert store.delete(memory_id) is True
    assert store.delete(memory_id) is False
    assert store.stats()["count"] == 0
