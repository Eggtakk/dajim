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
    """Raised when the aihubshell subprocess exits non-zero, or can't be
    found at all."""


@dataclass(frozen=True)
class DownloadResult:
    command: list[str]
    returncode: int


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
    config.data_dir (created if missing).

    stdout/stderr are inherited from this process rather than captured:
    aihubshell can run for minutes on a large dataset, prints its own
    progress, and may prompt for confirmation. Capturing its output would
    buffer all of that until the process exits, making a download that's
    actually working look hung. Letting it write straight to the terminal
    also means a stdin prompt from aihubshell reaches the user, since
    subprocess.run inherits stdin by default too.

    Raises AihubDownloadError if aihubshell exits non-zero or isn't found.
    """
    command = build_download_command(config, aihubshell_path)
    config.data_dir.mkdir(parents=True, exist_ok=True)

    try:
        completed = subprocess.run(
            command,
            cwd=config.data_dir,
            check=False,
        )
    except FileNotFoundError as exc:
        raise AihubDownloadError(
            f"'{aihubshell_path}'를 찾을 수 없습니다 — PATH에 aihubshell이 설치되어 "
            "있는지 확인하세요 (model/README.md의 설치 안내 참고)."
        ) from exc
    if completed.returncode != 0:
        raise AihubDownloadError(
            f"aihubshell exited with code {completed.returncode} — 위 출력에서 원인을 확인하세요."
        )
    return DownloadResult(command=command, returncode=completed.returncode)
