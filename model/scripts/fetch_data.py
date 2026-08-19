"""CLI: download the configured AI Hub dataset via aihubshell.

Usage (from model/):
    python -m scripts.fetch_data

Requires AIHUB_API_KEY to be set in model/.env (see model/.env.example) and
`aihubshell` on PATH.
"""
from __future__ import annotations

import sys

from data.aihub_client import AihubDownloadError, download
from data.config import load_config


def main() -> int:
    config = load_config()
    try:
        result = download(config)
    except (ValueError, AihubDownloadError) as exc:
        print(f"다운로드 실패: {exc}", file=sys.stderr)
        return 1

    print(f"다운로드 완료: {config.data_dir}")
    if result.stdout:
        print(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
