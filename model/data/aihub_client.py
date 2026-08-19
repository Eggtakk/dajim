"""Thin wrapper around the official `aihubshell` CLI for downloading files.

We shell out to aihubshell instead of re-implementing AI Hub's download
protocol: the underlying REST endpoints aren't publicly documented, and
aihubshell already handles multi-part downloads, decompression, and
directory re-assembly. See
docs/superpowers/specs/2026-08-19-aihub-spending-trend-design.md.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass

from .config import AihubConfig


class AihubDownloadError(RuntimeError):
    """Raised when the aihubshell subprocess exits non-zero."""


@dataclass(frozen=True)
class DownloadResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def build_download_command(config: AihubConfig, aihubshell_path: str = "aihubshell") -> list[str]:
    """Build the `aihubshell -mode d ...` argv for the configured dataset."""
    if not config.api_key:
        raise ValueError("AIHUB_API_KEY is not set — fill it in model/.env before downloading.")

    command = [
        aihubshell_path,
        "-mode", "d",
        "-datasetkey", config.dataset_key,
        "-aihubapikey", config.api_key,
    ]
    if config.file_keys:
        command += ["-filekey", ",".join(config.file_keys)]
    return command


def download(config: AihubConfig, aihubshell_path: str = "aihubshell") -> DownloadResult:
    """Run aihubshell to download the configured dataset/files into
    config.data_dir (created if missing). Raises AihubDownloadError if
    aihubshell exits non-zero."""
    command = build_download_command(config, aihubshell_path)
    config.data_dir.mkdir(parents=True, exist_ok=True)

    try:
        completed = subprocess.run(
            command,
            cwd=config.data_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise AihubDownloadError(
            f"'{aihubshell_path}'를 찾을 수 없습니다 — PATH에 aihubshell이 설치되어 "
            "있는지 확인하세요 (model/README.md의 설치 안내 참고)."
        ) from exc
    if completed.returncode != 0:
        raise AihubDownloadError(
            f"aihubshell exited with code {completed.returncode}: {completed.stderr}"
        )
    return DownloadResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
