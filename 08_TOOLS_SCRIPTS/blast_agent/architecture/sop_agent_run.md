# SOP: B.L.A.S.T. Agent Run Loop (sop_agent_run.md)

This Standard Operating Procedure (SOP) defines the execution, reasoning, and self-healing behaviors of the B.L.A.S.T. Local Agentic System.

---

## 1. Execution Protocol

The agent loop executes in five sequential phases, adhering strictly to the B.L.A.S.T. framework.

### Phase 1: Blueprint

1. Read `.context/active_brief.md` to identify active goals.
2. Read `gemini.md` to load the current state log and verified data schemas.
3. If new data inputs or external destinations are specified, verify their schemas before writing code.

### Phase 2: Link

1. Verify that all required environment variables and credentials in `.env` are loaded.
2. If keys are missing, halt execution and prompt the user.
3. Verify connection to active scraper targets using dry-run calls.

### Phase 3: Architect

1. Map out the sequence of tools required to achieve the brief's goals.
2. Execute Layer 3 tools (`tools/`) in order.
3. Save intermediate files, scrape results, and session states in `.tmp/`.

### Phase 4: Stylize

1. Parse all intermediate scraper outputs.
2. Format output structures into clean, professional Markdown reports or structured JSON payloads.
3. Save finalized deliverables under the designated target folders (e.g., `01_INGEST_INBOX/`).

### Phase 5: Trigger

1. Compile the run summary.
2. Append a 1-3 line context handoff to `gemini.md` describing what changed and what the next logical step is.
3. If configured, execute external notification triggers (e.g., Webhooks, Firebase deployment).

---

## 2. Self-Healing Automation (The Repair Loop)

When a Tool execution fails or returning output is malformed:

1. **Analyze**: Read the stack trace or output code. Do not guess.
2. **Patch**: Modify the Python code inside the `tools/` directory.
3. **Test**: Execute the tool in isolation to verify the patch.
4. **Document**: Update this SOP or `sop_scrapers.md` with the newly learned constraint so the error is prevented in future runs.
