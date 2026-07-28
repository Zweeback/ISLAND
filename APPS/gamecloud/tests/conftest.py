"""pytest configuration for APPS/gamecloud."""
import sys
from pathlib import Path

# Add the gamecloud root to PYTHONPATH so `src.*` imports resolve.
sys.path.insert(0, str(Path(__file__).parent.parent))
