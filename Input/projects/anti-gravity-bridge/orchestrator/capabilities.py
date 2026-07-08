import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ResourceRequirements(BaseModel):
    cpu_cores: int
    gpu_required: bool
    vram_mb: int

class Capability(BaseModel):
    id: str
    version: str
    owner: str
    input_schema: str
    output_schema: str
    timeout_sec: int
    dependencies: List[str] = Field(default_factory=list)
    healthcheck_command: str
    cost_hint: float
    resource_requirements: ResourceRequirements

class CapabilityRegistry:
    def __init__(self, capabilities_dir: Optional[str] = None):
        if capabilities_dir is None:
            # Resolve relative to the bridge workspace
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            capabilities_dir = os.path.join(base_dir, "capabilities")
        self.capabilities_dir = capabilities_dir
        self.capabilities: Dict[str, Capability] = {}
        self.load_capabilities()

    def load_capabilities(self):
        self.capabilities.clear()
        if not os.path.exists(self.capabilities_dir):
            return
        for file in os.listdir(self.capabilities_dir):
            if file.endswith(".json"):
                path = os.path.join(self.capabilities_dir, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        cap = Capability(**data)
                        self.capabilities[cap.id] = cap
                except Exception as e:
                    raise ValueError(f"Failed to parse capability file {file}: {e}")

    def get_capability(self, capability_id: str) -> Optional[Capability]:
        return self.capabilities.get(capability_id)

    def list_capabilities(self) -> List[Capability]:
        return list(self.capabilities.values())
