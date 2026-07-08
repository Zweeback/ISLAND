from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Literal

class DagNode(BaseModel):
    node_id: str
    command_type: str
    target: str
    depends_on: List[str] = Field(default_factory=list)
    payload_template: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

class DagRun(BaseModel):
    run_id: str
    nodes: List[DagNode]
    node_states: Dict[str, Literal["pending", "ready", "running", "completed", "failed", "skipped"]] = Field(default_factory=dict)
    artifacts: Dict[str, str] = Field(default_factory=dict)  # node_id -> output_path
    provenance: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")
