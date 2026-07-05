# ISLAND Agent Bridge API

Unified API for accessing all agents through Jules orchestrator

---

## Overview

All agent interactions go through Jules, which routes to the appropriate agent:

```
Client Request
    ↓
/api/agents/query (Jules)
    ├→ Route to CODEX
    ├→ Route to GEMINI
    ├→ Route to ANTIGRAVITY
    ├→ Route to RAG
    └→ Combine & return
```

---

## Base URL

```
http://localhost:3000/api/agents
```

---

## Endpoints

### 1. Process Query (Jules)

Route any query to appropriate agents.

```
POST /api/agents/query
```

**Request**:
```json
{
  "query": "Simulate rush hour in Dortmund",
  "intent": "simulation",
  "context": {
    "project": "gta-dortmund",
    "user_id": "user123"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "result": "Simulation started",
  "agents_used": ["codex", "rag", "gemini", "antigravity"],
  "execution_time_ms": 1234
}
```

---

### 2. Validate with Codex

```
POST /api/agents/codex/validate
```

**Request**:
```json
{
  "data": {
    "project": "new-game",
    "type": "simulation"
  },
  "schema": "project_config"
}
```

**Response**:
```json
{
  "valid": true,
  "errors": []
}
```

---

### 3. Generate Code with Gemini

```
POST /api/agents/gemini/generate
```

**Request**:
```json
{
  "prompt": "Generate a WebSocket server for multiplayer game",
  "language": "typescript",
  "context": "game-development"
}
```

**Response**:
```json
{
  "code": "import WebSocket from 'ws';\n...",
  "language": "typescript",
  "explanation": "This creates a WebSocket server...",
  "tokens_used": 456
}
```

---

### 4. Deploy with Antigravity

```
POST /api/agents/antigravity/deploy
```

**Request**:
```json
{
  "project_id": "gta-dortmund",
  "environment": "production",
  "resources": {
    "cpu": "2",
    "memory": "4Gi"
  }
}
```

**Response**:
```json
{
  "deployment_id": "dep-abc123",
  "status": "in_progress",
  "url": "https://gta-dortmund.island-game.dev",
  "estimated_time_seconds": 120
}
```

---

### 5. Retrieve Knowledge with RAG

```
POST /api/agents/rag/retrieve
```

**Request**:
```json
{
  "query": "What is the population of Dortmund?",
  "top_k": 5,
  "filters": {
    "source": "opendata_dortmund"
  }
}
```

**Response**:
```json
{
  "results": [
    {
      "text": "Dortmund population 2024: 587,181",
      "source": "opendata_dortmund",
      "relevance_score": 0.95,
      "url": "https://..."
    }
  ],
  "total_results": 12
}
```

---

### 6. Get Agent Status

```
GET /api/agents/status
```

**Response**:
```json
{
  "agents": {
    "jules": {
      "status": "healthy",
      "uptime_hours": 24,
      "requests_processed": 1234
    },
    "codex": {
      "status": "healthy",
      "rules_loaded": 42,
      "schemas_loaded": 15
    },
    "gemini": {
      "status": "healthy",
      "model": "gemini-pro",
      "api_available": true
    },
    "antigravity": {
      "status": "healthy",
      "gcp_connection": "active",
      "deployments_active": 5
    },
    "rag": {
      "status": "healthy",
      "documents_indexed": 1000,
      "vector_store_size": "2.5GB"
    }
  },
  "last_health_check": "2026-07-05T15:30:00Z"
}
```

---

### 7. Trigger Project

```
POST /api/agents/trigger
```

**Request**:
```json
{
  "project": "gta-dortmund",
  "command": "simulate",
  "parameters": {
    "scenario": "rush_hour",
    "agents": 500,
    "duration": "5min"
  }
}
```

**Response**:
```json
{
  "execution_id": "exec-xyz789",
  "status": "running",
  "progress": 0,
  "estimated_completion_seconds": 300
}
```

---

### 8. Get Execution Status

```
GET /api/agents/executions/{execution_id}
```

**Response**:
```json
{
  "execution_id": "exec-xyz789",
  "project": "gta-dortmund",
  "command": "simulate",
  "status": "running",
  "progress": 45,
  "elapsed_seconds": 135,
  "estimated_remaining_seconds": 165
}
```

---

## Error Handling

All endpoints return consistent error format:

```json
{
  "status": "error",
  "error": {
    "code": "AGENT_UNAVAILABLE",
    "message": "Gemini agent is currently unavailable",
    "suggestion": "Falling back to Codex engine",
    "details": "..."
  }
}
```

### Common Error Codes

| Code | Meaning | Fallback |
|------|---------|----------|
| `AGENT_UNAVAILABLE` | Agent not responding | Use fallback chain |
| `INVALID_SCHEMA` | Data doesn't match schema | Reject or ask Gemini |
| `PERMISSION_DENIED` | User not authorized | Return 403 |
| `TIMEOUT` | Agent took too long | Retry or escalate |
| `UNKNOWN_INTENT` | Can't determine action | Ask Jules or user |

---

## Authentication

All requests require API key:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://localhost:3000/api/agents/query \
  -d '{"query": "..."}'
```

---

## Rate Limiting

- **Free tier**: 100 requests/hour per agent
- **Pro tier**: 1000 requests/hour per agent
- **Enterprise**: Unlimited

---

## Examples

### Example 1: Query + RAG

```bash
curl -X POST http://localhost:3000/api/agents/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What data do we have about Dortmund?",
    "intent": "knowledge_retrieval"
  }'
```

### Example 2: Generate & Validate Code

```bash
curl -X POST http://localhost:3000/api/agents/gemini/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create API endpoint for user authentication",
    "language": "typescript"
  }' | \
  xargs -I {} curl -X POST http://localhost:3000/api/agents/codex/validate \
  -H "Content-Type: application/json" \
  -d '{
    "code": {},
    "schema": "typescript_api"
  }'
```

### Example 3: Deploy Project

```bash
curl -X POST http://localhost:3000/api/agents/antigravity/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "gta-dortmund",
    "environment": "production"
  }'
```

---

## WebSocket Support

For real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:3000/api/agents/stream');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Agent update:', update);
};

ws.send(JSON.stringify({
  command: 'trigger',
  project: 'gta-dortmund',
  action: 'simulate'
}));
```

---

**Version**: 1.0.0  
**Updated**: 2026-07-05
