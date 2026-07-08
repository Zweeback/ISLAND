from __future__ import annotations

import os
import sys
import uuid
import json
import hashlib
import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Literal, Optional

from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks,
)
from pydantic import BaseModel, ConfigDict, Field, field_validator

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
from orchestrator.deferred_queue import queue_depth

BASE_DIR = Path(parent_dir)
ARTIFACTS_DIR = BASE_DIR / "artifacts"
EVENTS_DIR = ARTIFACTS_DIR / "events"
JOBS_DIR = ARTIFACTS_DIR / "jobs"

EVENTS_DIR.mkdir(parents=True, exist_ok=True)
JOBS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
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
    mission_id: Optional[str] = None
    job_id: Optional[str] = None
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
    state: Literal["accepted", "running", "completed", "failed", "deferred", "retrying"]
    created_at: str
    updated_at: str
    dry_run: bool
    artifacts: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class LLMOutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: Literal[
        "blender.create_cube",
        "blender.render_scene",
        "meshroom.photogrammetry_reconstruct",
        "unity.sync_assets",
    ]
    scale: List[float] = Field(
        default_factory=lambda: [1.0, 1.0, 1.0], min_length=3, max_length=3
    )
    radius: float = Field(default=1.0, ge=0.01, le=100.0)
    output_path: str = Field(default="", max_length=240)

    @field_validator("scale")
    @classmethod
    def validate_scale_bounds(cls, value: List[float]) -> List[float]:
        if any(component < 0.01 or component > 100.0 for component in value):
            raise ValueError("scale components must be between 0.01 and 100.0")
        return value

    @field_validator("output_path")
    @classmethod
    def validate_output_path(cls, value: str) -> str:
        if not value:
            return value
        path = Path(value)
        if path.is_absolute() or any(part == ".." for part in path.parts):
            raise ValueError("output_path must be a safe relative path")
        return value


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


def _is_resource_defer_error(errors: List[str]) -> bool:
    return any(
        "insufficient_vram" in err or "insufficient_ram" in err for err in errors
    )


async def _emit(event: dict[str, Any]) -> None:
    append_event(event)
    await bus.broadcast(event)


async def execute_admitted_job(
    cmd: BridgeCommand, job_id: str, sm: JobStateMachine, state: JobState
) -> None:
    artifacts: List[str] = []
    errors: List[str] = []

    try:
        if cmd.dry_run:
            await asyncio.sleep(0.05)
            artifacts_jobs_dir = JOBS_DIR / job_id
            artifacts_jobs_dir.mkdir(parents=True, exist_ok=True)

            if cmd.target == "blender":
                art_file = f"blender_job_{cmd.command_type.split('.')[-1]}_{cmd.payload.get('model_name', 'model')}.glb"
                marker = artifacts_jobs_dir / art_file
                marker.write_text(
                    f"MOCK GLB DATA FOR ACTION {cmd.command_type}\n", encoding="utf-8"
                )
            elif cmd.target == "meshroom":
                art_file = f"meshroom_reconstruction_{cmd.payload.get('project_id', 'proj')}.obj"
                marker = artifacts_jobs_dir / art_file
                marker.write_text(
                    f"# MOCK OBJ RECONSTRUCTION FOR ACTION {cmd.command_type}\n",
                    encoding="utf-8",
                )
            else:
                marker = artifacts_jobs_dir / "dry_run.txt"
                marker.write_text("ok\n", encoding="utf-8")

            artifacts.append(f"artifacts/jobs/{job_id}/{marker.name}")
        else:
            loop = asyncio.get_running_loop()
            if cmd.target == "blender":
                action = cmd.command_type.split(".")[-1]
                result = await loop.run_in_executor(
                    None,
                    lambda: run_blender_command(action=action, payload=cmd.payload),
                )
                if result.get("success"):
                    artifacts = result.get("artifacts", [])
                else:
                    errors.append(result.get("error", "Unknown Blender error"))
            elif cmd.target == "meshroom":
                action = cmd.command_type.split(".")[-1]
                result = await loop.run_in_executor(
                    None,
                    lambda: run_meshroom_pipeline(action=action, payload=cmd.payload),
                )
                if result.get("success"):
                    artifacts = result.get("artifacts", [])
                else:
                    errors.append(result.get("error", "Unknown Meshroom error"))
            elif cmd.target == "unity":
                report_name = "unity_sync_report.json"
                report_path = JOBS_DIR / job_id / report_name
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(
                    '{"status": "success", "synced_assets_count": 0}\n',
                    encoding="utf-8",
                )
                artifacts.append(f"artifacts/jobs/{job_id}/{report_name}")
            else:
                errors.append(f"Unsupported target: {cmd.target}")
    except Exception as exc:
        errors.append(str(exc))

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

    artifacts_str = [str(art).replace("\\", "/") for art in artifacts]
    generate_provenance(
        job_id=job_id,
        command={"command_type": cmd.command_type, "payload": cmd.payload},
        input_files=input_files,
        output_files=artifacts_str,
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
        await _emit({"type": "job.failed", "job_id": job_id, "error": state.error})
    else:
        state.state = "completed"
        state.updated_at = utcnow()
        state.artifacts = artifacts_str
        write_job_state(state)
        try:
            sm.transition_to("succeeded", reason="Job completed successfully")
        except Exception:
            pass
        await _emit(
            {"type": "job.completed", "job_id": job_id, "artifacts": artifacts_str}
        )


async def retry_deferred_entry(entry: dict[str, Any]) -> None:
    from orchestrator.deferred_queue import (
        load_deferred_entry,
        save_deferred_entry,
        remove_deferred_entry,
    )
    from orchestrator.resource_manager import admit_job_with_recovery
    from orchestrator.retry_scheduler import mark_retry_scheduled, mark_retry_exhausted

    job_id = entry["job_id"]
    current = load_deferred_entry(job_id)
    if not current:
        return

    cmd = BridgeCommand(**current["command"])
    sm = JobStateMachine(job_id)
    if sm.state not in ("deferred", "retrying"):
        remove_deferred_entry(job_id)
        return

    state_data = json.loads(
        (JOBS_DIR / job_id / "job_state.json").read_text(encoding="utf-8")
    )
    state = JobState(
        job_id=job_id,
        command_id=state_data.get("command_id", cmd.command_id),
        target=cmd.target,
        command_type=cmd.command_type,
        state="retrying",
        created_at=state_data.get("created_at", utcnow()),
        updated_at=utcnow(),
        dry_run=cmd.dry_run,
        error=current.get("reason"),
    )

    try:
        sm.transition_to(
            "retrying", reason=f"Retry attempt {current['retry_count'] + 1}"
        )
    except Exception as exc:
        log.error("Failed transition to retrying for %s: %s", job_id, exc)
        current["dispatching"] = False
        save_deferred_entry(current)
        return

    state.state = "retrying"
    write_job_state(state)
    await _emit(
        {
            "type": "job.retrying",
            "job_id": job_id,
            "attempt": current["retry_count"] + 1,
        }
    )

    model_name = os.getenv("OLLAMA_RECOVERY_MODEL", "gemma4")
    admitted, reason, ollama_unloaded = await admit_job_with_recovery(
        cmd.target, cmd.command_type, model_name=model_name
    )
    if ollama_unloaded and admitted:
        await _emit(
            {
                "type": "job.ollama_unloaded",
                "job_id": job_id,
                "detail": f"Unloaded {model_name} model to satisfy job VRAM requirements",
            }
        )

    if not admitted:
        if current["retry_count"] + 1 >= current.get("max_retries", 5):
            try:
                sm.transition_to("failed", reason=f"retry_exhausted: {reason}")
            except Exception:
                pass
            state.state = "failed"
            state.error = f"retry_exhausted: {reason}"
            state.updated_at = utcnow()
            write_job_state(state)
            mark_retry_exhausted(current)
            await _emit(
                {"type": "job.retry_exhausted", "job_id": job_id, "error": state.error}
            )
            return

        try:
            sm.transition_to("deferred", reason=reason)
        except Exception:
            pass
        state.state = "deferred"
        state.error = reason
        state.updated_at = utcnow()
        write_job_state(state)
        mark_retry_scheduled(current, reason)
        await _emit({"type": "job.deferred", "job_id": job_id, "reason": reason})
        return

    remove_deferred_entry(job_id)
    try:
        sm.transition_to("running", reason="Resources available on retry")
    except Exception as exc:
        log.error("Failed transition to running for %s: %s", job_id, exc)
        return

    state.state = "running"
    state.updated_at = utcnow()
    state.error = None
    write_job_state(state)
    await _emit(
        {
            "type": "job.started",
            "job_id": job_id,
            "target": cmd.target,
            "command_type": cmd.command_type,
        }
    )
    await execute_admitted_job(cmd, job_id, sm, state)


async def run_job(cmd: BridgeCommand, job_id: str) -> None:
    started = utcnow()
    state = JobState(
        job_id=job_id,
        command_id=cmd.command_id,
        target=cmd.target,
        command_type=cmd.command_type,
        state="accepted",
        created_at=started,
        updated_at=started,
        dry_run=cmd.dry_run,
    )

    # State machine transition to validating -> ready -> running
    sm = JobStateMachine(job_id, initial_state="accepted")
    try:
        sm.transition_to(
            "validating", reason="Checking capability registration and payload"
        )
    except Exception as e:
        log.error(f"Failed state transition: {e}")

    event = {
        "type": "job.validating",
        "job_id": job_id,
        "target": cmd.target,
        "command_type": cmd.command_type,
    }
    append_event(event)
    await bus.broadcast(event)

    artifacts = []
    errors = []

    # 1. LLM Validation Gate
    if "llm_raw_text" in cmd.payload:
        raw_text = cmd.payload["llm_raw_text"]
        try:
            parsed_json = json.loads(raw_text)
            validated_output = LLMOutputModel(**parsed_json)
            # Safe payload transfer
            cmd.payload.clear()
            cmd.payload.update(validated_output.model_dump())
        except Exception as e:
            validation_error = f"failed_validation: {type(e).__name__}"
            errors.append(validation_error)
            event = {
                "type": "failed_validation",
                "job_id": job_id,
                "error": validation_error,
                "raw_text_sha256": hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
                "raw_text_length": len(raw_text),
            }
            append_event(event)
            await bus.broadcast(event)

    # 2. JIT Guard Resource check (with optional Ollama VRAM recovery)
    if not errors and not cmd.dry_run:
        from orchestrator.resource_manager import admit_job_with_recovery

        admission_event = {
            "type": "job.admission_check",
            "job_id": job_id,
            "target": cmd.target,
        }
        append_event(admission_event)
        await bus.broadcast(admission_event)

        model_name = os.getenv("OLLAMA_RECOVERY_MODEL", "gemma4")
        admitted, reason, ollama_unloaded = await admit_job_with_recovery(
            cmd.target, cmd.command_type, model_name=model_name
        )
        if ollama_unloaded and admitted:
            event = {
                "type": "job.ollama_unloaded",
                "job_id": job_id,
                "detail": f"Unloaded {model_name} model to satisfy job VRAM requirements",
            }
            append_event(event)
            await bus.broadcast(event)
        if not admitted:
            errors.append(reason)
            event = {"type": "job.deferred", "job_id": job_id, "reason": reason}
            append_event(event)
            await bus.broadcast(event)

    # State Machine transitions & Pydantic state writes
    if not errors:
        try:
            sm.transition_to("ready", reason="Capability verified")
            sm.transition_to("running", reason="Running background worker")
            state.state = "running"
            state.updated_at = utcnow()
            write_job_state(state)
            started_event = {
                "type": "job.started",
                "job_id": job_id,
                "target": cmd.target,
                "command_type": cmd.command_type,
            }
            append_event(started_event)
            await bus.broadcast(started_event)
        except Exception as e:
            log.error(f"Failed state transition: {e}")
    else:
        error_text = "; ".join(errors)
        if _is_resource_defer_error(errors):
            from orchestrator.deferred_queue import enqueue_deferred_job

            try:
                sm.transition_to("deferred", reason=error_text)
            except Exception as e:
                log.error(f"Failed state transition to deferred: {e}")
            state.state = "deferred"
            state.updated_at = utcnow()
            state.error = error_text
            write_job_state(state)
            enqueue_deferred_job(job_id, cmd.model_dump(), errors[0])
            return

        try:
            sm.transition_to("failed", reason=error_text)
            state.state = "failed"
            state.updated_at = utcnow()
            state.error = error_text
            write_job_state(state)
            await _emit({"type": "job.failed", "job_id": job_id, "error": state.error})
        except Exception as e:
            log.error(f"Failed state transition to failed: {e}")
        return

    await execute_admitted_job(cmd, job_id, sm, state)


_scheduler_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler_task
    from orchestrator.retry_scheduler import retry_scheduler_loop

    append_event({"type": "service.started", "service": settings.app_name})
    if os.environ.get("DISABLE_DEFERRED_SCHEDULER", "").lower() not in (
        "true",
        "1",
        "yes",
    ):
        if "pytest" not in sys.modules:
            _scheduler_task = asyncio.create_task(
                retry_scheduler_loop(retry_deferred_entry)
            )
    yield
    if _scheduler_task:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
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
        "queue_depth": queue_depth(),
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
    for line in lines[-max(1, min(limit, 1000)) :]:
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

    append_event(
        {
            "type": "legacy.command.received",
            "event": "CommandReceived",
            "command_id": cmd.command_id,
            "target": cmd.target,
            "action": cmd.action,
        }
    )
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
        command={
            "job_type": job.job_type,
            "payload": job.payload,
            "capability_id": capability_id,
        },
        input_files=[],
        output_files=[],
    )
    append_event(
        {
            "type": "legacy.job.queued",
            "event": "CommandReceived",
            "job_id": job_id,
            "job_type": job.job_type,
            "capability_id": capability_id,
        }
    )

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
        if state == "succeeded":
            data["state"] = "completed"
        else:
            data["state"] = state
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
    import argparse
    import asyncio
    import uvicorn

    parser = argparse.ArgumentParser(description="Anti-Gravity Bridge entry point")
    parser.add_argument(
        "command", nargs="?", default="runserver", help="runserver or run_dag"
    )
    args = parser.parse_args()

    if args.command == "run_dag":
        from orchestrator.dag_models import DagNode, DagRun
        from orchestrator.dag_executor import execute_dag

        dag = DagRun(
            run_id="run_" + uuid.uuid4().hex[:8],
            nodes=[
                DagNode(
                    node_id="mesh",
                    command_type="meshroom.photogrammetry_reconstruct",
                    target="meshroom",
                    payload_template={},
                ),
                DagNode(
                    node_id="blend",
                    command_type="blender.create_cube",
                    target="blender",
                    depends_on=["mesh"],
                    payload_template={},
                ),
                DagNode(
                    node_id="unity",
                    command_type="unity.sync_assets",
                    target="unity",
                    depends_on=["blend"],
                    payload_template={},
                ),
            ],
            node_states={},
            artifacts={},
            provenance={},
        )
        asyncio.run(execute_dag(dag))
        print("DAG execution completed. Node states:", dag.node_states)
    else:
        uvicorn.run("main:app", host="127.0.0.1", port=8420, reload=True)
