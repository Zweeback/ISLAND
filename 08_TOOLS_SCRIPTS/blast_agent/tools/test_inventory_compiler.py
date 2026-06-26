from .inventory_compiler import LocalIndexer


def test_inventory_compiler_regex_match():
    indexer = LocalIndexer([])
    assert indexer.should_exclude_file(".env") is True
    assert indexer.should_exclude_file("my_passwords.txt") is True
    assert indexer.should_exclude_file("some_id_rsa_key") is True
    assert indexer.should_exclude_file("secret_agent.bin") is True
    assert indexer.should_exclude_file("normal_file.txt") is False
