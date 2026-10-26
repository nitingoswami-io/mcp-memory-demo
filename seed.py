"""Seed the memory store with a handful of example memories.

Run once to try the demo without wiring up Claude Desktop first:
    uv run seed.py
"""
from __future__ import annotations

from memory_store import MemoryStore

SAMPLES = [
    {
        "content": "I prefer dark-roast single-origin coffee, especially from Ethiopia.",
        "tags": ["preferences", "food"],
        "source": "conversation",
    },
    {
        "content": "Project Atlas kicks off on Nov 3 — Priya is tech lead, Marco owns infra.",
        "tags": ["work", "project-atlas"],
        "source": "slack",
    },
    {
        "content": "Reading list: 'Designing Data-Intensive Applications' and 'Building a Second Brain'.",
        "tags": ["books", "learning"],
        "source": "notebook",
    },
    {
        "content": "Dentist appointment every six months; last visit was in September.",
        "tags": ["health", "schedule"],
        "source": "calendar",
    },
    {
        "content": "Favorite debugging trick: binary-search commits with git bisect before reaching for a debugger.",
        "tags": ["engineering", "tips"],
        "source": "notebook",
    },
]


def main() -> None:
    store = MemoryStore()
    for sample in SAMPLES:
        memory_id = store.add(**sample)
        print(f"stored {memory_id}: {sample['content'][:60]}...")
    print(f"\nTotal memories: {store.stats()['count']}")

    print("\nTrying a recall for 'what should I read next?':")
    for hit in store.search("what should I read next?", limit=3, tags=None):
        print(f"  [{hit['score']}] {hit['content']}")


if __name__ == "__main__":
    main()
