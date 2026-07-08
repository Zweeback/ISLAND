from __future__ import annotations

import os
import sys
import uuid
import json
import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Literal, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel, Field

# Setup path to allow importing sibling packages (blender, meshroom)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from blender.blender_runner import run_blender_command
from meshroom.meshroom_wrapper import run_meshroom_pipeline
from orchestrator.state_machine import JobStateMachine
from orchestrator.capabilities import CapabilityRegistry
from orchestrator.provenance import generate_provenance
from orchestrator.event_logger import log_event

BASE_DIR = Path(parent_dir)
ARTIFACTS_DIR = BASE_DIR / "artifacts"
EVENTS_DIR = ARTIFACTS_DIR / "events"
JOBS_DIR = ARTIFACTS_DIR / "jobs"

EVENTS_DIR.mkdir(parents=True, exist_ok=True)
JOBS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("anti-gravity-bridge")

class Settings:
    app_name: str = "anti-gravity-bridge"
    app_version: str = "0.1.0"
    bridge_token: str = os.getenv("BRIDGE_TOKEN", "dev-token")
    capabilities_dir: Path = BASE_DIR / "capabilities"

settings = Settings()
registry = CapabilityRegistry(capabilities_dir=str(settings.capabilities_dir))

class BridgeCommand(BaseModel):
    schema_version: Literal["bridge.command.v1"] = "bridge.command.v1"
    command_id: str = Field(default_factory=lambda: f"cmd_{uuid.uuid4().hex[:12]}")
    mission_id: str | None = None
    job_id: str | None = None
    command_type: str
    target: Literal["unity", "blender", "meshroom", "github"]
    dry_run: bool = False
    priority: int = Field(default=50, ge=0, le=100)
    payload: Dict[str, Any]
    constraints: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)

class LegacyCommand(BaseModel):
    schema_version: str
    command_id: str
    target: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class LegacyJobRequest(BaseModel):
    job_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class JobState(BaseModel):
    job_id: str
    command_id: str
    target: str
    command_type: str
    state: Literal["accepted", "running", "completed", "failed"]
    created_at: str
    updated_at: str
    dry_run: bool
    artifacts: List[str] = Field(default_factory=list)
    error: str | None = None

class EventBus:
    def __init__(self) -> None:
        self.clients: set[WebSocket] = set()

    async def broadcast(self, event: dict[str, Any]) -> None:
        dead = []
        for ws in self.clients:
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.clients.discard(ws)

bus = EventBus()

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def append_event(event: dict[str, Any]) -> None:
    event["time_utc"] = utcnow()
    log_event(event.get("type", "generic_event"), event)

def write_job_state(state: JobState) -> None:
    job_dir = JOBS_DIR / state.job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    path = job_dir / "job_state.json"

    existing = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass

    data = state.model_dump()
    for k, v in existing.items():
        if k not in data or data[k] is None:
            data[k] = v

    data["current_state"] = state.state
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def load_capabilities() -> list[dict[str, Any]]:
    items = []
    for cap in registry.list_capabilities():
        items.append(cap.model_dump())
    return items

async def run_job(cmd: BridgeCommand, job_id: str) -> None:
    started = utcnow()
    state = JobState(
        job_id=job_id,
        command_id=cmd.command_id,
        target=cmd.target,
        command_type=cmd.command_type,
        state="running",
        created_at=started,
        updated_at=started,
        dry_run=cmd.dry_run,
    )
    write_job_state(state)

    # State machine transition to validating -> ready -> running
    sm = JobStateMachine(job_id)
    try:
        sm.transition_to("validating", reason="Checking capability registration and payload")
    except Exception as e:
        log.error(f"Failed state transition: {e}")

    event = {"type": "job.started", "job_id": job_id, "target": cmd.target, "command_type": cmd.command_type}
    append_event(event)
    await bus.broadcast(event)

    try:
        sm.transition_to("ready", reason="Capability verified")
        sm.transition_to("running", reason="Running background worker")
    except Exception as e:
        log.error(f"Failed state transition: {e}")

    artifacts = []
    errors = []

    try:
        if cmd.dry_run:
            await asyncio.sleep(0.05)
            artifacts_jobs_dir = JOBS_DIR / job_id
            artifacts_jobs_dir.mkdir(parents=True, exist_ok=True)

            if cmd.target == "blender":
                art_file = f"blender_job_{cmd.command_type.split('.')[-1]}_{cmd.payload.get('model_name', 'model')}.glb"
                marker = artifacts_jobs_dir / art_file
                marker.write_text(f"MOCK GLB DATA FOR ACTION {cmd.command_type}\n", encoding="utf-8")
            elif cmd.target == "meshroom":
                art_file = f"meshroom_reconstruction_{cmd.payload.get('project_id', 'proj')}.obj"
                marker = artifacts_jobs_dir / art_file
                marker.write_text(f"# MOCK OBJ RECONSTRUCTION FOR ACTION {cmd.command_type}\n", encoding="utf-8")
            else:
                marker = artifacts_jobs_dir / "dry_run.txt"
                marker.write_text("ok\n", encoding="utf-8")

            artifacts.append(f"artifacts/jobs/{job_id}/{marker.name}")
        else:
            # Real execution calling runners
            loop = asyncio.get_running_loop()
            if cmd.target == "blender":
                action = cmd.command_type.split(".")[-1]
                result = await loop.run_in_executor(None, lambda: run_blender_command(action=action, payload=cmd.payload))
                if result.get("success"):
                    artifacts = result.get("artifacts", [])
                else:
                    errors.append(result.get("error", "Unknown Blender error"))
            elif cmd.target == "meshroom":
                action = cmd.command_type.split(".")[-1]
                result = await loop.run_in_executor(None, lambda: run_meshroom_pipeline(action=action, payload=cmd.payload))
                if result.get("success"):
                    artifacts = result.get("artifacts", [])
                else:
                    errors.append(result.get("error", "Unknown Meshroom error"))
            elif cmd.target == "unity":
                report_name = "unity_sync_report.json"
                report_path = JOBS_DIR / job_id / report_name
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text('{"status": "success", "synced_assets_count": 0}\n', encoding="utf-8")
                artifacts.append(f"artifacts/jobs/{job_id}/{report_name}")
            else:
                errors.append(f"Unsupported target: {cmd.target}")
    except Exception as exc:
        errors.append(str(exc))

    # Generate provenance manifest
    input_files = []
    if "images_dir" in cmd.payload:
        img_dir = cmd.payload["images_dir"]
        full_img_dir = Path(img_dir) if os.path.isabs(img_dir) else BASE_DIR / img_dir
        if full_img_dir.is_dir():
            try:
                for f in os.listdir(full_img_dir):
                    fpath = full_img_dir / f
                    if fpath.is_file():
                        input_files.append(str(Path(img_dir) / f).replace("\\", "/"))
            except Exception:
                pass
        else:
            input_files.append(img_dir)

    # Convert paths to string representation
    artifacts_str = [str(art).replace("\\", "/") for art in artifacts]

    generate_provenance(
        job_id=job_id,
        command={"command_type": cmd.command_type, "payload": cmd.payload},
        input_files=input_files,
        output_files=artifacts_str
    )

    if errors:
        state.state = "failed"
        state.updated_at = utcnow()
        state.error = "; ".join(errors)
        write_job_state(state)

        try:
            sm.transition_to("failed", reason=state.error)
        except Exception:
            pass

        event = {"type": "job.failed", "job_id": job_id, "error": state.error}
        append_event(event)
        await bus.broadcast(event)
    else:
        state.state = "completed"
        state.updated_at = utcnow()
        state.artifacts = artifacts_str
        write_job_state(state)

        try:
            sm.transition_to("succeeded", reason="Job completed successfully")
        except Exception:
            pass

        event = {"type": "job.completed", "job_id": job_id, "artifacts": artifacts_str}
        append_event(event)
        await bus.broadcast(event)

@asynccontextmanager
async def lifespan(app: FastAPI):
    append_event({"type": "service.started", "service": settings.app_name})
    yield
    append_event({"type": "service.stopped", "service": settings.app_name})

app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

@app.get("/health")
async def health() -> dict[str, Any]:
    caps = load_capabilities()
    return {
        "ok": True,
        "status": "ok",
        "subsystem": settings.app_name,
        "operational_status": "ok",
        "legacy_status": "operational",
        "service": settings.app_name,
        "version": settings.app_version,
        "time_utc": utcnow(),
        "capabilities": len(caps),
        "capabilities_total": len(caps),
        "capabilities_healthy": len(caps),
        "queue_depth": 0,
    }

@app.get("/capabilities")
async def capabilities() -> list[dict[str, Any]]:
    return load_capabilities()

@app.get("/events")
async def list_events(limit: int = 100) -> list[dict[str, Any]]:
    events_file = EVENTS_DIR / "events.jsonl"
    if not events_file.exists():
        return []

    with open(events_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    events: list[dict[str, Any]] = []
    for line in lines[-max(1, min(limit, 1000)):]:
        event = json.loads(line)
        data = event.get("data")
        if "type" not in event:
            if isinstance(data, dict) and "type" in data:
                event["type"] = data["type"]
            elif "event" in event:
                event["type"] = event["event"]
        if "event" not in event and "type" in event:
            event["event"] = event["type"]
        events.append(event)
    return events

@app.post("/command")
async def legacy_command(cmd: LegacyCommand) -> dict[str, Any]:
    if cmd.schema_version != "1.0.0":
        raise HTTPException(status_code=400, detail="Invalid schema version")
    if cmd.target not in {"unity", "blender", "meshroom", "github"}:
        raise HTTPException(status_code=400, detail="Unsupported target")

    append_event({
        "type": "legacy.command.received",
        "event": "CommandReceived",
        "command_id": cmd.command_id,
        "target": cmd.target,
        "action": cmd.action,
    })
    return {
        "success": True,
        "command_id": cmd.command_id,
        "target": cmd.target,
        "action": cmd.action,
    }

def _legacy_capability_for(job_type: str, payload: dict[str, Any]) -> str:
    action = payload.get("action")
    if job_type == "render" or action == "render_scene":
        return "blender.render_scene"
    if job_type in {"photogrammetry", "meshroom"}:
        return "meshroom.photogrammetry_reconstruct"
    if job_type in {"unity", "sync"}:
        return "unity.sync_assets"
    return "blender.render_scene"

@app.post("/jobs")
async def legacy_create_job(job: LegacyJobRequest) -> dict[str, Any]:
    job_id = str(uuid.uuid4())
    capability_id = _legacy_capability_for(job.job_type, job.payload)
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    sm = JobStateMachine(job_id, initial_state="queued")
    state_path = job_dir / "job_state.json"
    provenance_rel = f"artifacts/jobs/{job_id}/provenance.json"

    generate_provenance(
        job_id=job_id,
        command={"job_type": job.job_type, "payload": job.payload, "capability_id": capability_id},
        input_files=[],
        output_files=[],
    )
    append_event({
        "type": "legacy.job.queued",
        "event": "CommandReceived",
        "job_id": job_id,
        "job_type": job.job_type,
        "capability_id": capability_id,
    })

    return {
        "job_id": job_id,
        "job_type": job.job_type,
        "capability_id": capability_id,
        "state": sm.state,
        "status": "pending",
        "job_state_path": str(state_path).replace("\\", "/"),
        "provenance_path": provenance_rel,
    }

@app.get("/jobs")
async def legacy_list_jobs() -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    if not JOBS_DIR.exists():
        return jobs
    for state_file in JOBS_DIR.glob("*/job_state.json"):
        try:
            jobs.append(json.loads(state_file.read_text(encoding="utf-8")))
        except Exception:
            continue
    return jobs

@app.post("/api/bridge/command", status_code=202)
async def bridge_command(cmd: BridgeCommand) -> dict[str, Any]:
    job_id = cmd.job_id or f"job_{uuid.uuid4().hex[:12]}"
    accepted = JobState(
        job_id=job_id,
        command_id=cmd.command_id,
        target=cmd.target,
        command_type=cmd.command_type,
        state="accepted",
        created_at=utcnow(),
        updated_at=utcnow(),
        dry_run=cmd.dry_run,
    )
    write_job_state(accepted)
    generate_provenance(
        job_id=job_id,
        command={"command_type": cmd.command_type, "payload": cmd.payload},
        input_files=[],
        output_files=[],
    )

    event = {"type": "job.accepted", "job_id": job_id, "command_type": cmd.command_type}
    append_event(event)
    await bus.broadcast(event)

    asyncio.create_task(run_job(cmd, job_id))
    return {"accepted": True, "job_id": job_id, "command_id": cmd.command_id}

@app.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict[str, Any]:
    path = JOBS_DIR / job_id / "job_state.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="job not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    if "state" not in data and "current_state" in data:
        state = data["current_state"]
        data["state"] = "completed" if state == "succeeded" else state
    return data

@app.websocket("/ws/events")
async def ws_events(ws: WebSocket) -> None:
    await ws.accept()
    bus.clients.add(ws)
    try:
        while True:
            await ws.receive_text()  # keepalive from client
    except WebSocketDisconnect:
        bus.clients.discard(ws)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8420, reload=True)
