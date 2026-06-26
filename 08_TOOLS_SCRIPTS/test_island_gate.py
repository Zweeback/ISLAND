import json
from pathlib import Path

import pytest

from island_gate import iter_jsonl


def test_iter_jsonl_missing_file(tmp_path):
    missing_file = tmp_path / "missing.jsonl"
    records, errors = iter_jsonl(missing_file)
    assert records == []
    assert len(errors) == 1
    assert errors[0] == f"missing file: {missing_file}"


def test_iter_jsonl_valid(tmp_path):
    valid_file = tmp_path / "valid.jsonl"
    valid_file.write_text(
        '{"id": "1", "name": "foo"}\n'
        '\n'
        '{"id": "2", "name": "bar"}\n',
        encoding="utf-8"
    )
    records, errors = iter_jsonl(valid_file)
    assert errors == []
    assert len(records) == 2
    assert records[0] == {"id": "1", "name": "foo"}
    assert records[1] == {"id": "2", "name": "bar"}


def test_iter_jsonl_invalid_json(tmp_path):
    invalid_file = tmp_path / "invalid.jsonl"
    invalid_file.write_text(
        '{"id": "1"}\n'
        '{"id": "2", "name": foo}\n'
        '{"id": "3"}\n',
        encoding="utf-8"
    )
    records, errors = iter_jsonl(invalid_file)
    assert len(records) == 2
    assert records[0] == {"id": "1"}
    assert records[1] == {"id": "3"}
    assert len(errors) == 1
    assert "invalid.jsonl:2: invalid json" in errors[0]


def test_iter_jsonl_not_object(tmp_path):
    not_object_file = tmp_path / "not_object.jsonl"
    not_object_file.write_text(
        '{"id": "1"}\n'
        '["not", "an", "object"]\n'
        '"just a string"\n'
        '{"id": "2"}\n',
        encoding="utf-8"
    )
    records, errors = iter_jsonl(not_object_file)
    assert len(records) == 2
    assert records[0] == {"id": "1"}
    assert records[1] == {"id": "2"}
    assert len(errors) == 2
    assert "not_object.jsonl:2: record is not an object" in errors[0]
    assert "not_object.jsonl:3: record is not an object" in errors[1]
