# Anti-Gravity Bridge: Command & Job Schema Documentation

This document describes how to build, route, and parse command inputs and job states within the Anti-Gravity Bridge.

## Direct Command API

Direct commands are synchronous instructions dispatched to the `/command` endpoint.

* **URL:** `POST /command`
* **Content-Type:** `application/json`

### Direct Command Request Payload
```json
{
  "schema_version": "1.0.0",
  "command_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3d4b2d",
  "target": "blender",
  "action": "render_scene",
  "payload": {
    "model_name": "Spaceship",
    "engine": "CYCLES"
  }
}
```

### Direct Command Success Response
```json
{
  "success": true,
  "message": "Blender dry-run simulated successfully for action 'render_scene'.",
  "artifacts": [
    "artifacts/jobs/blender_job_render_scene_Spaceship.glb"
  ]
}
```

---

## Background Job API

Background jobs are long-running actions (e.g. photogrammetry) managed as async tasks.

* **Create Job URL:** `POST /jobs`
* **Response Payload (Job Model):**
```json
{
  "job_id": "f516a8d6-44c0-43db-8f8a-f5e6b7c89a0b",
  "job_type": "photogrammetry",
  "status": "running",
  "progress": 10.0,
  "payload": {
    "action": "photogrammetry_reconstruct",
    "images_dir": "C:/Users/derzw/Photos/ObjectPhotos",
    "project_id": "house_scan_01"
  },
  "artifacts": [],
  "errors": [],
  "created_at": "2026-07-08T15:30:00Z",
  "updated_at": "2026-07-08T15:30:10Z"
}
```

* **Query Status URL:** `GET /jobs/{job_id}`
* **Response Payload (Completed Job):**
```json
{
  "job_id": "f516a8d6-44c0-43db-8f8a-f5e6b7c89a0b",
  "job_type": "photogrammetry",
  "status": "completed",
  "progress": 100.0,
  "payload": {
    "action": "photogrammetry_reconstruct",
    "images_dir": "C:/Users/derzw/Photos/ObjectPhotos",
    "project_id": "house_scan_01"
  },
  "artifacts": [
    "artifacts/jobs/meshroom_reconstruction_house_scan_01.obj"
  ],
  "errors": [],
  "created_at": "2026-07-08T15:30:00Z",
  "updated_at": "2026-07-08T15:31:45Z"
}
```
