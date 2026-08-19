from pathlib import Path

from data.config import load_config


def test_load_config_parses_comma_separated_file_keys(monkeypatch):
    monkeypatch.setenv("AIHUB_API_KEY", "test-key")
    monkeypatch.setenv("AIHUB_DATASET_KEY", "71792")
    monkeypatch.setenv("AIHUB_FILE_KEYS", "111, 222,333")
    monkeypatch.setenv("AIHUB_DATA_DIR", "/tmp/aihub-data")

    config = load_config()

    assert config.api_key == "test-key"
    assert config.dataset_key == "71792"
    assert config.file_keys == ["111", "222", "333"]
    assert config.data_dir == Path("/tmp/aihub-data")


def test_load_config_defaults_when_unset(monkeypatch):
    monkeypatch.delenv("AIHUB_API_KEY", raising=False)
    monkeypatch.delenv("AIHUB_DATASET_KEY", raising=False)
    monkeypatch.delenv("AIHUB_FILE_KEYS", raising=False)
    monkeypatch.delenv("AIHUB_DATA_DIR", raising=False)

    config = load_config()

    assert config.api_key is None
    assert config.dataset_key == "71792"
    assert config.file_keys == []
    assert config.data_dir == Path("./data/raw")
