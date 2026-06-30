import pytest
from pathlib import Path
import sys

# Add tools directory to path to allow import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.inventory_compiler import LocalIndexer


@pytest.fixture
def indexer():
    """Returns a LocalIndexer instance with dummy paths for testing."""
    return LocalIndexer([Path("/dummy/path")])


class TestLocalIndexerShouldExcludeFile:

    @pytest.mark.parametrize(
        "file_name",
        [
            # Exact pattern matches
            ".env",
            "passwords",
            "id_rsa",
            "secret",
            # Suffix/prefix/substring variations
            ".env.example",
            ".env.local",
            "my_passwords.txt",
            "passwords_backup.zip",
            "my_id_rsa",
            "id_rsa.pub",
            "my_secret_key",
            "secret.txt",
            "top_secret_document.pdf",
            # Case-insensitivity tests
            ".ENV",
            ".Env",
            "PaSsWoRdS",
            "PASSWORDS.TXT",
            "ID_RSA",
            "id_RSA.pub",
            "SECRET",
            "Secret.txt",
            "MY_SECRET_FILE.DOCX",
        ],
    )
    def test_should_exclude_file_returns_true_for_excluded_patterns(
        self, indexer, file_name
    ):
        """Test that files matching excluded patterns are correctly identified for exclusion."""
        assert indexer.should_exclude_file(file_name) is True

    @pytest.mark.parametrize(
        "file_name",
        [
            # Normal files (happy path)
            "script.py",
            "README.md",
            "main.c",
            "index.html",
            "style.css",
            "data.json",
            "image.png",
            # Similar but not quite matching
            "env.py",  # Missing dot for .env
            "environment.yml",  # No .env
            "password",  # Missing 's' in passwords
        ],
    )
    def test_should_exclude_file_returns_false_for_normal_files(
        self, indexer, file_name
    ):
        """Test that normal files are not excluded."""
        assert indexer.should_exclude_file(file_name) is False

    @pytest.mark.parametrize(
        "file_name",
        [
            # Note: the current logic uses simple `in` which will match these,
            # even if they might not be intended (like "secretary" containing "secret").
            # This documents the current behavior.
            "secretary.doc"
        ],
    )
    def test_current_behavior_edge_cases(self, indexer, file_name):
        """Documents the current behavior where simple substring matching might over-exclude."""
        assert indexer.should_exclude_file(file_name) is True
