# ISLAND Setup Scripts - Free Tier Optimized

**Purpose**: Automated setup for local + cloud orchestration  
**Constraint**: Copilot Free (limited usage)  
**Strategy**: Lightweight, cost-efficient, minimal dependencies

---

## Quick Start (5 minutes)

```bash
# 1. Clone ISLAND
git clone https://github.com/Zweeback/ISLAND.git
cd ISLAND

# 2. Run setup
bash AGENTS/scripts/setup.sh

# 3. Done! Your system is ready
```

---

## 1. GCS Setup (Free Tier)

### Create Free Google Cloud Project

```bash
# Set up gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Create project (FREE)
gcloud projects create island-project
gcloud config set project island-project

# Enable APIs (always free tier)
gcloud services enable compute.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

### Create Storage Bucket (Free Tier)

```bash
# Create bucket - 5GB free storage
gsutil mb gs://island-assets-free

# Set lifecycle policy to auto-delete old files (save space)
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://island-assets-free
```

### Install GCSFuse (Mount Bucket Locally)

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y gcsfuse

# On macOS
brew install gcsfuse

# Mount bucket
mkdir -p ~/island-assets
gcsfuse --implicit-dirs island-assets-free ~/island-assets

# Test
ls ~/island-assets
# Should work!
```

---

## 2. Docker Setup (Free)

### Install Docker (Free)

```bash
# Ubuntu/Debian
sudo apt-get install -y docker.io

# macOS
# Download Docker Desktop (free): https://www.docker.com/products/docker-desktop

# Start Docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

### Minimal Blender Container

```dockerfile
# AGENTS/docker/Dockerfile.blender
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Install only what we need (keep small)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    blender \
    python3 \
    python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install Google Cloud Storage client
RUN pip install google-cloud-storage

WORKDIR /workspace
COPY render_script.py /workspace/

ENTRYPOINT ["blender", "-b"]
CMD ["-P", "/workspace/render_script.py"]
```

### Build & Push to Free Registry

```bash
# Use Docker Hub (free, unlimited public images)
docker build -f AGENTS/docker/Dockerfile.blender -t yourusername/island-blender:latest .
docker push yourusername/island-blender:latest

# Or use GitHub Container Registry (free)
docker build -f AGENTS/docker/Dockerfile.blender -t ghcr.io/yourusername/island-blender:latest .
docker push ghcr.io/yourusername/island-blender:latest
```

---

## 3. Asset Watcher (Python, Lightweight)

```python
# AGENTS/orchestration/asset_watcher.py

import os
import time
from pathlib import Path
from google.cloud import storage

class AssetWatcher:
    def __init__(self, local_dir, bucket_name):
        self.local_dir = Path(local_dir)
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.watched_files = {}
    
    def get_file_hash(self, file_path):
        """Quick file change detection"""
        return os.path.getmtime(file_path)
    
    def watch_directory(self, watch_path):
        """Monitor directory for changes"""
        for file_path in Path(watch_path).rglob("*"):
            if file_path.is_file():
                file_hash = self.get_file_hash(file_path)
                
                # File is new or changed
                if str(file_path) not in self.watched_files or \
                   self.watched_files[str(file_path)] != file_hash:
                    
                    self.watched_files[str(file_path)] = file_hash
                    self.sync_to_gcs(file_path)
    
    def sync_to_gcs(self, file_path):
        """Upload file to GCS"""
        try:
            relative_path = file_path.relative_to(self.local_dir)
            blob = self.bucket.blob(str(relative_path))
            blob.upload_from_filename(file_path)
            print(f"✓ Synced: {relative_path}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def start_watching(self, check_interval=30):
        """Run continuous watch loop"""
        print(f"Watching {self.local_dir}...")
        try:
            while True:
                self.watch_directory(self.local_dir)
                time.sleep(check_interval)
        except KeyboardInterrupt:
            print("\nWatcher stopped")

if __name__ == "__main__":
    watcher = AssetWatcher(
        local_dir=os.path.expanduser("~/island-assets"),
        bucket_name="island-assets-free"
    )
    watcher.start_watching()
```

### Run Asset Watcher

```bash
# Install dependency
pip install google-cloud-storage

# Start watching
python AGENTS/orchestration/asset_watcher.py

# Or run in background
nohup python AGENTS/orchestration/asset_watcher.py > watcher.log 2>&1 &
```

---

## 4. Jules Configuration (Free APIs Only)

```json
{
  "AGENTS/JULES/config.json": {
    "orchestrator": "jules",
    "version": "1.0.0",
    "execution_mode": "local_first_cloud_fallback",
    
    "ai_backends": {
      "gemini_free": {
        "provider": "Google Gemini",
        "model": "gemini-pro",
        "api_key": "$GEMINI_API_KEY",
        "free_tier": true,
        "rate_limit": "60/minute",
        "cost": "$0 (free tier)",
        "fallback_rank": 1
      },
      "codex_rules": {
        "provider": "Local",
        "model": "rule_engine",
        "free_tier": true,
        "cost": "$0",
        "fallback_rank": 0
      }
    },
    
    "execution_environments": {
      "local_gpu": {
        "type": "workstation",
        "cost": "$0 (hardware owned)",
        "use_for": "quick jobs, real-time",
        "fallback_rank": 0
      },
      "gcp_free_tier": {
        "type": "google_cloud",
        "always_free": true,
        "includes": "1 e2-micro VM + 5GB storage",
        "cost": "$0 (always free)",
        "use_for": "small batch jobs"
      },
      "docker_local": {
        "type": "container",
        "cost": "$0",
        "use_for": "containerized processing"
      }
    },
    
    "cost_optimization": {
      "prefer_local": true,
      "batch_cloud_jobs": true,
      "run_during_free_tier_hours": true,
      "max_monthly_cost": 0
    }
  }
}
```

---

## 5. Minimal Setup Script

```bash
#!/bin/bash
# AGENTS/scripts/setup.sh

set -e

echo "=== ISLAND Setup (Free Tier) ==="

# 1. GCS Setup
echo "1. Setting up Google Cloud Storage..."
gsutil mb gs://island-assets-free 2>/dev/null || echo "   (Bucket may already exist)"

# 2. Mount GCS Locally
echo "2. Mounting GCS bucket..."
mkdir -p ~/island-assets
gcsfuse --implicit-dirs island-assets-free ~/island-assets &
sleep 2
echo "   ✓ Mounted at ~/island-assets"

# 3. Install Python dependencies
echo "3. Installing Python dependencies..."
pip install -q google-cloud-storage watchdog

# 4. Create necessary directories
echo "4. Creating directories..."
mkdir -p AGENTS/orchestration/logs
mkdir -p AGENTS/docker
mkdir -p 08_TOOLS_SCRIPTS/scripts

# 5. Set up environment
echo "5. Setting up .env..."
cat > .env << EOF
GEMINI_API_KEY=your-api-key-here
GCP_PROJECT_ID=island-project
GCS_BUCKET=gs://island-assets-free
EOF

echo "6. Creating startup script..."
cat > start_island.sh << 'SCRIPT'
#!/bin/bash
echo "Starting ISLAND..."
python AGENTS/orchestration/asset_watcher.py &
echo "Asset watcher running (PID: $!)"
echo "✓ ISLAND ready!"
SCRIPT
chmod +x start_island.sh

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Set GEMINI_API_KEY in .env"
echo "2. Run: ./start_island.sh"
echo "3. Access assets at: ~/island-assets"
echo ""
echo "Free resources:"
echo "✓ 5GB GCS storage (always free)"
echo "✓ 1 e2-micro VM (always free)"
echo "✓ Gemini API (free tier: 60 req/min)"
echo "✓ Local Docker (free)"
echo ""
```

---

## 6. Running Locally (No Cloud Costs)

### Option A: 100% Local (Cheapest)

```bash
# Everything runs on your machine
# No cloud costs at all

# 1. Start asset watcher
python AGENTS/orchestration/asset_watcher.py &

# 2. Work in Blender/Meshroom/Unity locally
blender my_scene.blend &
# meshroom ...
# unity ...

# 3. Assets auto-sync to GCS (for backup only)
# No cloud processing needed
```

### Option B: Local + Free Cloud (Recommended)

```bash
# Local: Quick work (Blender preview, small Meshroom projects)
# Cloud: Heavy lifting (only when needed, free tier VM)

# Start the system
./start_island.sh

# Jules decides automatically:
# - Small task? Run locally (instant)
# - Large task? Use free GCP VM (5GB storage, e2-micro always free)
```

---

## 7. Free Tier Limits & Strategy

```
RESOURCE                  FREE TIER              STRATEGY
─────────────────────────────────────────────────────────────
Google Cloud Storage      5 GB                   → Delete old files auto
Compute Engine VM         1 e2-micro instance    → Light batch jobs only
Gemini API               60 requests/minute      → Queue queries, batch process
Docker                   Unlimited               → Use public Docker Hub
Python/Local GPU         Unlimited               → Do heavy work here
```

**Best Practice for Free Tier**:
- Work locally → Results are instant & free
- Use cloud only for unavoidable tasks → Batch them together
- Run cloud jobs at night → Better queuing
- Delete old assets regularly → Stay under 5GB limit

---

## 8. Copilot Free Integration

Since you have Copilot Free:

✅ **What Copilot Free Can Do**:
- Answer questions about your ISLAND setup
- Suggest improvements
- Debug errors
- Explain concepts
- Limited code generation

❌ **What Needs Manual Work**:
- Some complex multi-step code requires you to review/approve
- Large refactoring might hit usage limits
- Multi-file changes might need to be done step-by-step

**How to Maximize Copilot Free**:
1. Ask focused questions (not entire projects)
2. Paste errors → Copilot suggests fixes
3. Ask "how do I...?" → Get explanations
4. Use for debugging, not generation

---

## 9. Dockerfile for Minimal Setup

```dockerfile
# AGENTS/docker/Dockerfile.minimal
# Smallest possible image (useful for free tier limited resources)

FROM python:3.10-slim

# Install only essentials
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies
RUN pip install --no-cache-dir \
    google-cloud-storage \
    watchdog \
    click

WORKDIR /app
COPY . .

ENTRYPOINT ["python"]
```

Build:
```bash
docker build -f AGENTS/docker/Dockerfile.minimal -t island-lite:latest .
```

---

## 10. Troubleshooting

### GCS Mount Not Working

```bash
# Check if gcsfuse is installed
which gcsfuse

# Try remounting
fusermount -u ~/island-assets
gcsfuse --implicit-dirs island-assets-free ~/island-assets
```

### Out of GCS Storage

```bash
# Check usage
gsutil du -s gs://island-assets-free

# Delete old files
gsutil -m rm -r gs://island-assets-free/*.backup
```

### Gemini API Key Not Working

```bash
# Get your free API key
# https://ai.google.dev

# Set it
export GEMINI_API_KEY="your-key-here"

# Test
curl -X GET "https://generativelanguage.googleapis.com/v1beta/models?key=$GEMINI_API_KEY"
```

---

## Summary: Free Tier Setup

```
COST BREAKDOWN:
├─ GCS Storage: $0 (5GB free)
├─ Compute VM: $0 (e2-micro always free)
├─ Gemini API: $0 (60 req/min free)
├─ Docker: $0 (free)
├─ Local GPU: $0 (you own it)
└─ TOTAL: $0/month
```

**Your System**:
- ✅ Local work (instant, free)
- ✅ Asset backup (GCS, free)
- ✅ Light cloud jobs (e2-micro, free)
- ✅ AI queries (Gemini, 60/min free)
- ✅ Orchestration (Jules, free)

**Start command**:
```bash
bash AGENTS/scripts/setup.sh
./start_island.sh
```

---

**Status**: Free tier optimized setup complete  
**Cost**: $0/month (always free resources only)  
**Updated**: 2026-07-05
