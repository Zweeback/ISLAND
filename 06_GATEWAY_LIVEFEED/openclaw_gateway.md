# OpenClaw Gateway Candidate

Status: optional candidate integration
Required for consolidation: no
Previous known host: Asus Vivobook V16
Current working host: MSI G75 9SC

## Purpose

OpenClaw may become a gateway/bridge for live-feed or external automation work. It is not required for the repository consolidation branch because the consolidation can proceed with stable app homes, manifests, and Jules routing without choosing a gateway implementation.

## Migration Context

The OpenClaw gateway was previously available on the Asus Vivobook V16. This work is being performed from the MSI G75 9SC, so the gateway should be treated as an external component to rediscover or reconnect later, not as a local dependency that must exist on this machine today.

## Decision Rule

Adopt OpenClaw only if it provides a concrete gateway role that is not already covered by existing ISLAND scripts or Jules tooling.

## Future Integration Home

If adopted, OpenClaw integration files should live under `06_GATEWAY_LIVEFEED/openclaw/` with configuration referenced from `AGENTS/JULES/config.json`.
