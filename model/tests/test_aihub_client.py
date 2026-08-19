from pathlib import Path
from unittest.mock import patch

import pytest

from data.aihub_client import (
    AihubDownloadError,
    build_download_command,
    download,
)
from data.config import AihubConfig


def _config(**overrides) -> AihubConfig:
    defaults = dict(
        api_key="test-key",
        dataset_key="71792",
        file_keys=[],
        data_dir=Path("/tmp/aihub-data"),
    )
    defaults.update(overrides)
    return AihubConfig(**defaults)


def test_build_download_command_without_file_keys():
    command = build_download_command(_config())
    assert command == [
        "aihubshell", "-mode", "d",
        "-datasetkey", "71792",
        "-aihubapikey", "test-key",
    ]


def test_build_download_command_with_file_keys():
    command = build_download_command(_config(file_keys=["111", "222"]))
    assert command[-2:] == ["-filekey", "111,222"]


def test_build_download_command_requires_api_key():
    with pytest.raises(ValueError, match="AIHUB_API_KEY"):
        build_download_command(_config(api_key=None))


def test_download_raises_on_nonzero_exit(tmp_path):
    config = _config(data_dir=tmp_path)
    with patch("data.aihub_client.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        with pytest.raises(AihubDownloadError, match="exited with code 1"):
            download(config)


def test_download_returns_result_on_success(tmp_path):
    config = _config(data_dir=tmp_path)
    with patch("data.aihub_client.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        result = download(config)
    assert result.returncode == 0
    assert tmp_path.exists()


def test_download_does_not_capture_output(tmp_path):
    """aihubshell's own progress/prompts must reach the real terminal live —
    capturing stdout/stderr would buffer them until the process exits,
    making a working download look hung (see fix/aihub-download-stream-output)."""
    config = _config(data_dir=tmp_path)
    with patch("data.aihub_client.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        download(config)
    _, kwargs = mock_run.call_args
    assert "capture_output" not in kwargs
    assert "stdout" not in kwargs
    assert "stderr" not in kwargs


def test_download_raises_clear_error_when_aihubshell_missing(tmp_path):
    config = _config(data_dir=tmp_path)
    with patch("data.aihub_client.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("[Errno 2] No such file or directory: 'aihubshell'")
        with pytest.raises(AihubDownloadError, match="aihubshell.*PATH"):
            download(config)
