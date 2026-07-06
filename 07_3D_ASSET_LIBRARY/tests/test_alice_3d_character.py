import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alice_3d_character import ALICE3D


def test_load_model():
    alice = ALICE3D()

    result = alice.load_model("new_model.glb")
    assert alice.model_path == "new_model.glb"
    assert result is alice

    result2 = alice.load_model("another.glb", "new_texture.png")
    assert alice.model_path == "another.glb"
    assert alice.texture_path == "new_texture.png"
    assert result2 is alice
