# Contributing

Thanks for taking a look. This is a learning template, so the most useful
contributions make it **easier to understand or easier to adapt**: clearer
docs, another vector store or embedding model behind the existing
`MemoryStore` methods, a new MCP resource, better tests, or bug fixes.

## Fork, branch, pull request

1. **Fork** the repo: https://github.com/nitingoswami-io/mcp-memory-demo/fork
2. **Clone your fork** and add the original as `upstream`:
   ```bash
   git clone https://github.com/<you>/mcp-memory-demo.git
   cd mcp-memory-demo
   git remote add upstream https://github.com/nitingoswami-io/mcp-memory-demo.git
   ```
3. **Branch** from `main`: `git checkout -b <short-topic>`.
4. **Make the change**, with tests where behaviour changes.
5. **Run the checks** below.
6. **Push** to your fork and **open a pull request** against `main`. Fill in the template.

Keep your fork current with `git fetch upstream && git rebase upstream/main`.

## Getting set up

Requires Python 3.10+ and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
uv run seed.py          # 5 sample memories + one recall
uv run server.py        # stdio; add --http for http://127.0.0.1:8000/mcp
```

No API keys are needed. The first run downloads the embedding model (about
80 MB) into `~/.cache/chroma`; after that the tests run offline.

## Before opening a pull request

```bash
uv run python -m compileall -q server.py memory_store.py seed.py
uv run pytest -q
```

CI runs the same commands on every pull request.

## Guidelines

- **Keep it small and readable.** `server.py` is the MCP surface and
  `memory_store.py` is the store. Prefer a comment that says *why* over a
  clever abstraction.
- **Stay local-first.** The default setup must keep working with no API key
  and no hosted service. A hosted embedding model or database is welcome as an
  option, off by default and documented.
- **Write tool descriptions for the model.** The docstrings and `Field`
  descriptions in `server.py` are what the model reads to decide when to call
  a tool. Changes to them change behaviour; say so in the PR.
- **Never commit secrets or personal data.** `.env*` files and `data/` are
  ignored, except `.env.example`.

## Bugs and questions

Open an issue with one of the templates.

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
