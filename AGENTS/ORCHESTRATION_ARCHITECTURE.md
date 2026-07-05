# ISLAND Orchestration Architecture: Local + Cloud Hybrid

**Purpose**: Unified orchestration of local tools (Blender, Unity, Meshroom) with cloud infrastructure (Antigravity, AI Studio)

**Best Practice**: Use **Antigravity as primary orchestrator** with automated asset sync & trigger-based processing

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                              │
│                    (Jules + Antigravity CLI)                         │
│  - Decides: local vs cloud execution                                │
│  - Monitors asset changes                                           │
│  - Triggers workflows automatically                                 │
└────────┬────────────────────────────────────┬───────────────────────┘
         │                                    │
         ▼                                    ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│   LOCAL WORKSTATION (GPU)    │   │   CLOUD INFRASTRUCTURE (GCP) │
├──────────────────────────────┤   ├──────────────────────────────┤
│ • Blender (modeling)         │   │ • Antigravity GPU VMs        │
│ • Meshroom (photogrammetry)  │   │ • AI Studio (inference)      │
│ • Unity (game assembly)      │   │ • Cloud Storage buckets      │
│ • Local inference engine     │   │ • Distributed compute        │
│                              │   │ • Auto-scaling               │
│ Direct attached GPU          │   │ Managed, on-demand           │
│ Fast real-time work          │◄──►   Heavy batch processing     │
└──────────────────────────────┘   └──────────────────────────────┘
         ▲                                    │
         │                    ┌───────────────┘
         │                    │
         └────────────────────┘
         
    ASSET SYNC (Google Cloud Storage)
    ├─ Meshroom → GCS bucket
    ├─ Blender exports → GCS bucket
    ├─ Unity builds → GCS bucket
    └─ Cloud results → GCS bucket (synced back)
```

---

## 1. Antigravity as Primary Orchestrator

### Why Antigravity?

✅ **Managed Compute**: Spin up GPU VMs without manual config  
✅ **AI Studio Integration**: Native Gemini/LLM support  
✅ **Scalability**: Auto-scale from 1 to 100+ workers  
✅ **Cost Control**: Pay-per-minute, no upfront costs  
✅ **Google Cloud Native**: Works seamlessly with GCS, Firebase, etc.  

### Antigravity Control Flow

```
TASK ARRIVES
    │
    ▼
Jules decides:
├─ Local only? → Execute on Blender/Meshroom/Unity locally
├─ Cloud only? → Submit job to Antigravity
└─ Hybrid? → Local processing + cloud GPU acceleration
    │
    ▼
Antigravity orchestrates:
├─ Provision GPU VM (gcloud compute instances create)
├─ Mount shared GCS bucket
├─ Run Docker container with tool (Blender, custom script)
├─ Auto-scale if needed
├─ Monitor execution
├─ Sync results back to GCS
└─ Tear down when done (save cost)
```

---

## 2. Tool Integration Map

### Local Tools → Cloud Equivalents

```json
{
  "tools": {
    "blender": {
      "local": {
        "type": "desktop",
        "gpu": "RTX 3090 / A100",
        "use_for": "quick iterations, real-time preview",
        "latency": "instant"
      },
      "cloud": {
        "type": "docker_container",
        "gpu": "V100 / A100 / H100",
        "use_for": "batch rendering, heavy simulations",
        "latency": "2-5 minutes (spin-up)",
        "provider": "Antigravity (gcloud compute)"
      }
    },
    "meshroom": {
      "local": {
        "use_for": "small photogrammetry jobs (<100 images)",
        "latency": "real-time"
      },
      "cloud": {
        "use_for": "large projects (1000+ images), parallel processing",
        "docker_image": "alicevision/meshroom:latest",
        "provider": "Antigravity GPU cluster"
      }
    },
    "unity": {
      "local": {
        "use_for": "development, scene editing",
        "cli_mode": "headless builds"
      },
      "cloud": {
        "use_for": "automated builds, asset importers",
        "docker_image": "custom_unity:latest",
        "cli": "unity -quit -batchmode -executeMethod BuildScript.Build",
        "provider": "Antigravity"
      }
    },
    "custom_ai_inference": {
      "local": {
        "use_for": "fast inference, small models",
        "models": ["codex", "small_llms"]
      },
      "cloud": {
        "use_for": "large model inference, upscaling, super-resolution",
        "models": ["ESRGAN", "Stable Diffusion", "Gemini"],
        "provider": "AI Studio GPU nodes"
      }
    }
  }
}
```

---

## 3. Asset Synchronization Strategy

### Google Cloud Storage (GCS) as Central Hub

```
LOCAL FILES                GCS BUCKET              CLOUD PROCESSING
(Workstation)              (Sync Hub)              (Antigravity)

meshroom/
├─ input/                  gcsfuse mount ←→ /tmp/meshroom_input/
│  └─ photos/                                      ├─ Docker container
└─ output/                                         ├─ Process
    └─ mesh.ply            ←────────────────→      └─ Upload result

blender/                                           
├─ scene.blend             Auto-detect change      GPU-accelerated render
└─ exports/                Trigger cloud job       ├─ Batch mode
    └─ model.fbx           Upload to GCS           └─ Result back to GCS

unity/
├─ Assets/                                         Headless build
└─ Builds/                                         ├─ Import assets
                                                   └─ Create artifact
```

### Sync Mechanism

```python
# AGENTS/orchestration/asset_sync.py

class AssetSynchronizer:
    def __init__(self):
        self.gcs_bucket = "gs://island-assets"
        self.watch_dirs = [
            "/local/meshroom/output",
            "/local/blender/exports",
            "/local/unity/builds"
        ]
    
    def watch_for_changes(self):
        """Monitor local directories and auto-sync to GCS"""
        for directory in self.watch_dirs:
            self.monitor_with_watchdog(directory)
            # On file change:
            # 1. Upload to GCS
            # 2. Trigger associated cloud job
            # 3. Store metadata in RAG
    
    def trigger_cloud_processing(self, asset_type, file_path):
        """Submit job to Antigravity"""
        job = {
            "tool": asset_type,  # "meshroom", "blender", "unity"
            "input_path": file_path,
            "gcs_bucket": self.gcs_bucket,
            "docker_image": self.get_docker_image(asset_type),
            "resources": {
                "cpu": "8",
                "memory": "32Gi",
                "gpu": "1"
            }
        }
        self.submit_to_antigravity(job)
```

---

## 4. Docker Containers for Each Tool

### Pre-built Container Images

```dockerfile
# Docker images for cloud execution

# Blender rendering
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y blender
COPY render_script.py /render.py
ENTRYPOINT ["blender", "-b", "-P", "/render.py"]

# Meshroom photogrammetry
FROM alicevision/meshroom:2023.1.0
RUN apt-get update && apt-get install -y google-cloud-storage
COPY process_photogrammetry.py /process.py
ENTRYPOINT ["python", "/process.py"]

# Unity headless build
FROM unityci/editor:ubuntu-2022.3.0f1-linux-il2cpp
COPY build_project.cs /Assets/Editor/BuildScript.cs
ENTRYPOINT ["unity", "-quit", "-batchmode", "-executeMethod", "BuildScript.Build"]
```

---

## 5. Workflow Examples

### Workflow 1: Photogrammetry → AI Upscaling → Game Integration

```
LOCAL                           CLOUD                          RESULT
────────────────────────────────────────────────────────────────────
User captures
100+ photos
    │
    ├─ Upload to GCS
    │
    └─ Trigger Meshroom
                            ┌─ Antigravity spins up
                            ├─ Docker: Meshroom container
                            ├─ Process photogrammetry
                            ├─ Generate mesh.ply
                            │
                            ├─ Trigger AI upscaling
                            ├─ ESRGAN super-resolution
                            ├─ PBR texture generation
                            │
                            └─ Sync result to GCS
                                    │
                                    └─ Auto-download to local
                                       │
                                       ├─ Import into Blender
                                       ├─ Fine-tune materials
                                       │
                                       └─ Export to FBX
                                            │
                                            └─ Import to Unity
                                               │
                                               └─ GAME ASSET ✓
```

### Workflow 2: Game Build Pipeline

```
Developer commits to Git
    │
    ├─ GitHub Actions trigger
    │
    ├─ Download assets from GCS
    │
    ├─ Submit to Antigravity:
    │  {
    │    "docker": "unityci/editor",
    │    "script": "BuildScript.Build",
    │    "platforms": ["Linux", "WebGL"],
    │    "gpu_required": false
    │  }
    │
    └─ Antigravity:
       ├─ Spin up compute instance
       ├─ Mount GCS bucket (assets)
       ├─ Run headless Unity build
       ├─ Generate .exe / .wasm / .apk
       └─ Upload to GCS / Deploy
```

### Workflow 3: Real-Time Development with Cloud Assist

```
You're modeling in Blender
    │
    ├─ Auto-save to GCS (every 5 min)
    │
    ├─ Background: Antigravity renders preview
    │  └─ GPU-accelerated, high quality
    │
    └─ Result streams back to local
       └─ You see updated render while working
```

---

## 6. Configuration: Tools & Execution Strategy

```json
{
  "orchestration": {
    "primary_orchestrator": "antigravity",
    "fallback": "local",
    "auto_scaling": true
  },
  
  "execution_rules": {
    "blender": {
      "quick_render": {
        "threshold_size_mb": 100,
        "execute_on": "local",
        "timeout_seconds": 60
      },
      "heavy_render": {
        "threshold_size_mb": 1000,
        "execute_on": "antigravity",
        "gpu_type": "V100",
        "timeout_seconds": 3600
      }
    },
    "meshroom": {
      "small_project": {
        "image_count": 100,
        "execute_on": "local",
        "timeout_seconds": 1800
      },
      "large_project": {
        "image_count": 1000,
        "execute_on": "antigravity",
        "workers": 8,
        "timeout_seconds": 7200
      }
    },
    "unity": {
      "quick_build": {
        "size_mb": 500,
        "execute_on": "local",
        "platforms": ["WebGL"]
      },
      "full_build": {
        "size_mb": 5000,
        "execute_on": "antigravity",
        "platforms": ["Linux", "Windows", "WebGL"]
      }
    }
  },
  
  "asset_sync": {
    "gcs_bucket": "gs://island-assets",
    "auto_sync": true,
    "sync_interval": 300,
    "watched_directories": [
      "/local/meshroom/output",
      "/local/blender/exports",
      "/local/unity/builds"
    ],
    "enable_gcsfuse": true
  },
  
  "triggers": {
    "file_created": "auto_submit_to_cloud",
    "file_modified": "auto_submit_to_cloud",
    "schedule": "daily_optimization"
  }
}
```

---

## 7. Setup Instructions

### Step 1: Install GCS Fuse (Mount Cloud Bucket Locally)

```bash
# Mount GCS bucket as local filesystem
gcsfuse --implicit-dirs island-assets /mnt/island-assets

# Now you can access cloud files like local:
# /mnt/island-assets/meshroom/output/mesh.ply
```

### Step 2: Docker Images Setup

```bash
# Build & push Blender container
docker build -t gcr.io/island-project/blender:latest .
docker push gcr.io/island-project/blender:latest

# Same for Meshroom, Unity, etc.
```

### Step 3: Set Up Asset Watcher

```bash
# Run asset synchronizer
python AGENTS/orchestration/asset_sync.py

# Watches for changes and triggers cloud jobs automatically
```

### Step 4: Configure Jules for Antigravity

```bash
# Set up authentication
gcloud auth login
gcloud config set project island-project

# Jules now has access to spin up VMs, manage jobs, etc.
```

---

## 8. Cost Optimization

### Smart Execution Decision

```
Task arrives
│
├─ Quick task (< 5 min)?
│  └─ Execute locally (save cost, faster)
│
├─ Heavy task (> 30 min)?
│  ├─ Use Antigravity preemptible GPU ($0.30/hour vs $2/hour)
│  └─ Parallelize if possible
│
└─ Off-peak hours (2 AM)?
   └─ Batch non-urgent jobs (cheaper rates)
```

---

## 9. Monitoring & Logs

```bash
# View all jobs
gcloud compute instances list

# Monitor Antigravity jobs
gcloud compute operations list

# View asset sync logs
tail -f AGENTS/orchestration/logs/sync.log

# Jules orchestration logs
tail -f AGENTS/JULES/logs/orchestration.log
```

---

## Summary: Your Optimal Setup

```
┌─ LOCAL WORKSTATION
│  ├─ Blender (quick iterations)
│  ├─ Meshroom (small projects)
│  ├─ Unity (dev)
│  └─ Watcher → Auto-sync to GCS
│
├─ GCS BUCKET
│  └─ Central sync point
│
└─ ANTIGRAVITY (Primary Orchestrator)
   ├─ GPU VMs for heavy tasks
   ├─ Auto-scale
   ├─ Pull from GCS, process, sync back
   └─ Cost-optimized execution
```

**Best Practice Flow**:
1. Work locally (Blender/Meshroom/Unity)
2. Save to GCS (automatic via gcsfuse)
3. Antigravity detects changes
4. Auto-triggers cloud processing
5. Results sync back to local
6. Repeat ✓

---

**Next Steps**:
- [ ] Set up GCS bucket
- [ ] Install gcsfuse locally
- [ ] Build Docker images
- [ ] Configure asset watcher
- [ ] Test end-to-end workflow
- [ ] Set up cost monitoring

---

**Status**: Best-practice architecture defined  
**Last Updated**: 2026-07-05
