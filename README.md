# mcp-memory-demo

A minimal **MCP (Model Context Protocol) server** that gives any MCP-compatible
LLM client (Claude Desktop, Cursor, Zed, your own agent) a **RAG-backed
personal memory**.

It's intentionally small — one file for the MCP surface, one file for the RAG
store — so you can read it in ten minutes and extend it in an afternoon.

## What it demonstrates

- The **tool / resource split** that makes an MCP server pleasant for an LLM
  to use.
- A **local RAG pipeline** (ChromaDB + the default MiniLM embedding) with
  zero API keys and zero servers.
- Both **stdio** and **streamable HTTP** transports from the same codebase.

## Architecture

```
             ┌─────────────────────────┐
             │   LLM client            │
             │   (Claude Desktop,      │
             │    Cursor, agent, …)    │
             └───────────┬─────────────┘
                         │  MCP (stdio or HTTP)
                         ▼
             ┌─────────────────────────┐
             │  server.py              │   FastMCP, exposes:
             │                         │     tool: remember
             │                         │     tool: recall
             │                         │     tool: list_recent
             │                         │     tool: forget
             │                         │     resource: memory://stats
             └───────────┬─────────────┘
                         ▼
             ┌─────────────────────────┐
             │  memory_store.py        │   Thin RAG wrapper:
             │                         │     add / search / list / delete
             └───────────┬─────────────┘
                         ▼
             ┌─────────────────────────┐
             │  ChromaDB (local file)  │   persistent, cosine HNSW,
             │  ./data/chroma/         │   all-MiniLM-L6-v2 embeddings
             └─────────────────────────┘
```

## Quick start

Prerequisite: Python 3.10+ and [`uv`](https://docs.astral.sh/uv/)
(or plain `pip`).

```bash
# clone and enter the project
git clone <your-fork-url> mcp-memory-demo
cd mcp-memory-demo

# install dependencies
uv sync
# — or —
pip install -e .
```

Seed some demo memories and watch recall work:

```bash
uv run seed.py
```

Start the MCP server (stdio, for local LLM clients):

```bash
uv run server.py
```

Or over streamable HTTP, for remote clients:

```bash
uv run server.py --http
```

## Hooking it up to Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or the equivalent on your OS, and merge in:

```json
{
  "mcpServers": {
    "personal-memory": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-demo",
        "run",
        "server.py"
      ]
    }
  }
}
```

Restart Claude Desktop. You should now see the four `personal-memory` tools in
the hammer icon. Try prompting:

> *"Remember that I'm allergic to shellfish."*
> *"What did I say about my project kickoff?"*

A template config lives at [`examples/claude_desktop_config.json`](examples/claude_desktop_config.json).

## Tools exposed by this server

| Tool          | Purpose                                                                         |
| ------------- | ------------------------------------------------------------------------------- |
| `remember`    | Store a memory with optional tags and source.                                   |
| `recall`      | Semantic search over all memories; optional tag filter; returns similarity.     |
| `list_recent` | Reverse-chronological list — the LLM uses this when you ask "what did I just…". |
| `forget`      | Delete a memory by id.                                                          |

Resources:

| URI               | Returns                              |
| ----------------- | ------------------------------------ |
| `memory://stats`  | Plain-text store summary (count, path, collection). |

## Where to extend this

- **Swap the embedding model.** ChromaDB accepts any
  [embedding function](https://docs.trychroma.com/embeddings) — plug in OpenAI,
  Voyage, Cohere, or a local Ollama embedder for better retrieval quality.
- **Add hybrid search.** Combine BM25 (via `rank_bm25`) with the vector score
  before returning the top-k. Big quality lift on short queries.
- **Expose memory collections as MCP resources.** Right now only stats is a
  resource; "projects", "people", or "last 24h" could each become a browsable
  resource URI the LLM can read without a tool call.
- **Multi-tenancy.** For a hosted/enterprise version, scope each
  Chroma collection by user id, require OAuth 2.1 on the HTTP transport,
  and add audit logs.
- **Deterministic filters.** Pure vector search misses things like "last
  Tuesday" — add `created_at` range and `source` filters.

## License

MIT — do whatever you like with it.
