# Island MVP RAG Seed

This short document describes the **Zentrale Insel** governance model, the new JSONL manifest format, the live‑status contract, and the gatekeeper script. It is intended as the first ingestable knowledge source for the RAG pipeline.

- Manifest v2 uses strict JSONL, object identity, SHA256 hashes, trust levels and dependencies.
- Live status contract defines heartbeat, expiry and claim‑registry verification.
- The gatekeeper (`island_gate.py`) validates both manifests and service‑status records before any service may be marked `online_verified`.

The document is deliberately concise to keep the initial vector store small while still covering the core concepts.
