"""MCP server exposing a RAG-backed personal memory to LLM clients.

Run locally:
    uv run server.py              # stdio transport (Claude Desktop, Cursor, etc.)
    uv run server.py --http       # streamable HTTP transport (remote clients)
"""
from __future__ import annotations

import sys
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from memory_store import MemoryStore

mcp = MCPServer("personal-memory")
store = MemoryStore()


@mcp.tool()
def remember(
    content: Annotated[str, Field(description="The memory text to store.")],
    tags: Annotated[
        list[str] | None,
        Field(description="Optional tags for filtering later, e.g. ['work', 'idea'].")
    ] = None,
    source: Annotated[
        str | None,
        Field(description="Optional provenance, e.g. 'slack', 'notebook', 'conversation'.")
    ] = None,
) -> dict:
    """Store a new memory. Returns the generated memory id."""
    memory_id = store.add(content=content, tags=tags or [], source=source)
    return {"id": memory_id, "status": "stored"}


@mcp.tool()
def recall(
    query: Annotated[str, Field(description="Natural-language query to search memories.")],
    limit: Annotated[int, Field(description="Max results to return.", ge=1, le=50)] = 5,
    tags: Annotated[
        list[str] | None,
        Field(description="If set, only return memories tagged with any of these.")
    ] = None,
) -> list[dict]:
    """Semantically search stored memories. Returns the top matches with similarity scores."""
    return store.search(query=query, limit=limit, tags=tags)


@mcp.tool()
def list_recent(
    limit: Annotated[int, Field(description="Max results.", ge=1, le=100)] = 10,
) -> list[dict]:
    """List the most recent memories in reverse chronological order."""
    return store.list_recent(limit=limit)


@mcp.tool()
def forget(
    memory_id: Annotated[str, Field(description="The id of the memory to delete.")],
) -> dict:
    """Delete a memory by id. Returns whether a memory was actually removed."""
    deleted = store.delete(memory_id)
    return {"id": memory_id, "deleted": deleted}


@mcp.resource("memory://stats")
def stats() -> str:
    """A plain-text summary of the memory store state."""
    s = store.stats()
    return (
        "Personal memory store\n"
        f"- total memories: {s['count']}\n"
        f"- collection: {s['collection']}\n"
        f"- storage path: {s['path']}\n"
    )


def main() -> None:
    if "--http" in sys.argv:
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
