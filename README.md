# Claims Status Assistant

This project explains claim status in simple English.

You can ask things like:
- Why was claim `C-50012` denied for member `M10023`?
- Why was a claim paid?
- Why is a claim still pending?

The app looks up claim data, member data, and denial code details, then gives back a plain-language explanation with a few policy references.

## What this project uses

- `FastAPI` for the API
- `LangGraph` to run the claim explanation workflow step by step
- `MCP` so the graph can call claims, member, and denial-code tools through one interface
- `Chroma` for policy retrieval
- `Anthropic` for the final explanation

## How it works

1. A question comes into the API.
2. The graph extracts the claim ID and member ID.
3. The app fetches claim and member information through MCP.
4. If the claim is denied, it also looks up the denial code.
5. It retrieves related policy content from Chroma.
6. The LLM writes a plain-English explanation.
7. The API returns the final structured response.

## Run locally

Install dependencies:

```bash
uv sync
```

Activate the environment:

```bash
source .venv/bin/activate
```

Create a `.env` file in the project root and add:

```env
ANTHROPIC_API_KEY=your_key_here
```

Ingest the policy files into Chroma:

```bash
python -m scripts.ingest
```

Start the MCP server in one terminal:

```bash
python -m scripts.run_mcp_server
```

Start the API in another terminal:

```bash
python -m uvicorn src.main:app --reload --port 8000
```

## Test it

Health check:

```bash
curl http://localhost:3001/healthz
curl http://localhost:8000/healthz
```

Example request:

```bash
curl -X POST http://localhost:8000/v1/claims/explain \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{
    "question": "Why was claim C-50012 denied for member M10023?",
    "agent_id": "AGT-001"
  }'
```

## Docker

Run both services with Docker:

```bash
docker compose up --build
```

Then test the same endpoints on:
- `http://localhost:3001`
- `http://localhost:8000`

## Project structure

- `src/main.py`
  FastAPI app entrypoint

- `src/api/routes.py`
  API routes

- `src/graph/`
  LangGraph workflow and nodes

- `src/mcp/`
  MCP client, server, and tool handlers

- `src/tools/`
  Claims, member, denial code, and mock data clients

- `src/rag/`
  Policy retrieval and prompts

- `src/models/`
  API and domain models

- `src/security/`
  Auth, redaction, and audit logging

- `scripts/`
  Local helper scripts like ingestion and MCP startup

- `tests/`
  Pytest tests

## Notes

- `MOCK_MODE=true` is used for local development.
- The graph talks to backend tools through MCP, not by importing service clients directly.
- Policy documents need to be ingested before retrieval works properly.

## Example use cases

- denied claim explanation
- paid claim explanation
- pending claim status explanation
- denial code lookup with policy support
