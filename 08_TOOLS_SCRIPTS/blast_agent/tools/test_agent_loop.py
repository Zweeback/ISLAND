import pytest
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from agent_loop import load_env

def test_load_env_valid(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY1=value1\nKEY2=value2\n", encoding="utf-8")

    env = load_env(env_file)
    assert env == {"KEY1": "value1", "KEY2": "value2"}

def test_load_env_with_comments_and_blank_lines(tmp_path):
    env_file = tmp_path / ".env"
    content = """
# This is a comment
KEY1=value1

# Another comment
KEY2=value2
"""
    env_file.write_text(content, encoding="utf-8")

    env = load_env(env_file)
    assert env == {"KEY1": "value1", "KEY2": "value2"}

def test_load_env_with_equals_in_value(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=postgres://user:pass@localhost:5432/db?param=value=yes\n", encoding="utf-8")

    env = load_env(env_file)
    assert env == {"DATABASE_URL": "postgres://user:pass@localhost:5432/db?param=value=yes"}

def test_load_env_spaces_around_key_and_value(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("  KEY1  =  value1  \n\tKEY2\t=\tvalue2\t\n", encoding="utf-8")

    env = load_env(env_file)
    assert env == {"KEY1": "value1", "KEY2": "value2"}

def test_load_env_missing_file(tmp_path):
    env_file = tmp_path / ".env_nonexistent"

    env = load_env(env_file)
    assert env == {}

def test_load_env_no_equals_sign(tmp_path):
    env_file = tmp_path / ".env"
    content = """
KEY1=value1
INVALID_LINE_WITHOUT_EQUALS
KEY2=value2
"""
    env_file.write_text(content, encoding="utf-8")

    env = load_env(env_file)
    assert env == {"KEY1": "value1", "KEY2": "value2"}
