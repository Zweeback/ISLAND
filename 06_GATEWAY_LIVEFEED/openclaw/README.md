# OpenClaw Gateway

Status: candidate bridge
Previous host: Asus Vivobook V16
Current host: MSI G75 9SC
Required now: no

## Why This Exists

The user may need a gateway layer to coordinate agents and source feeds across machines. OpenClaw is the named candidate because it existed on the previous Asus Vivobook V16 setup.

## Proposed Responsibilities

OpenClaw should be used only if it can do one or more of these jobs better than the current ISLAND scripts:

- route events from RSS/source feeds into `06_GATEWAY_LIVEFEED/`
- bridge work between machines without hardcoded local paths
- expose a safe task queue for Jules/Codex/Gemini-style agents
- record what ran, where it ran, and what it changed
- pause or require approval before destructive or paid actions

## Minimum Contract

Any OpenClaw implementation should provide:

- append-only event log
- machine identity fields, e.g. `host`, `platform`, `workspace_root`
- task status fields: `queued`, `running`, `blocked`, `done`, `failed`
- source provenance for every feed or task
- no secrets committed to Git

## Not Yet Implemented

This folder currently defines the integration contract. Runtime code should be added only after the old Asus setup or a fresh OpenClaw source is available.
