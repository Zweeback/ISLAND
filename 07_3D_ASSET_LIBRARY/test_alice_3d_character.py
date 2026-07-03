import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "."))
import pytest
from alice_3d_character import ALICE3D

def test_load_model_path_only():
    alice = ALICE3D()
    result = alice.load_model("new_model.glb")
    assert alice.model_path == "new_model.glb"
    assert alice.texture_path == "07_3D_ASSET_LIBRARY/alice_texture.png" # default texture path
    assert result is alice

def test_load_model_with_texture():
    alice = ALICE3D()
    result = alice.load_model("new_model.glb", "new_texture.png")
    assert alice.model_path == "new_model.glb"
    assert alice.texture_path == "new_texture.png"
    assert result is alice

def test_load_model_with_none_texture():
    alice = ALICE3D()
    result = alice.load_model("new_model.glb", None)
    assert alice.model_path == "new_model.glb"
    assert alice.texture_path == "07_3D_ASSET_LIBRARY/alice_texture.png"
    assert result is alice
