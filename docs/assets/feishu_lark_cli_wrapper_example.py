#!/usr/bin/env python3
"""
Minimal public example: wrap lark-cli for user-scoped Feishu operations.

This file is intentionally sanitized:
- no real app ids
- no secrets
- no resource tokens
- no personal paths

Prerequisites:
- lark-cli installed
- user already authenticated via `lark-cli auth login`
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any


class LarkCLIError(RuntimeError):
    pass


def run_lark_cli(args: list[str], *, capture_output: bool = True) -> Any:
    """Run lark-cli and return parsed JSON when possible."""
    cmd = ["lark-cli", *args]
    env = os.environ.copy()

    result = subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        env=env,
    )

    if result.returncode != 0:
        raise LarkCLIError(
            f"lark-cli failed (exit {result.returncode}): {result.stderr.strip()}"
        )

    if not capture_output:
        return None

    stdout = result.stdout.strip()
    if not stdout:
        return None

    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return stdout


def check_auth_status() -> Any:
    return run_lark_cli(["auth", "status"])


def create_document(title: str, markdown_content: str) -> Any:
    return run_lark_cli([
        "docs", "+create",
        "--title", title,
        "--markdown", markdown_content,
    ])


def fetch_document(doc_id: str) -> Any:
    return run_lark_cli([
        "docs", "+fetch",
        "--doc-id", doc_id,
    ])


def search_documents(query: str) -> Any:
    return run_lark_cli([
        "docs", "+search",
        "--query", query,
    ])


def generic_api(method: str, path: str, *, params: dict | None = None, data: dict | None = None) -> Any:
    args = ["api", method, path]
    if params:
        args.extend(["--params", json.dumps(params, ensure_ascii=False)])
    if data:
        args.extend(["--data", json.dumps(data, ensure_ascii=False)])
    return run_lark_cli(args)


if __name__ == "__main__":
    status = check_auth_status()
    print("Auth status:", status)

    # Example (safe placeholder usage only)
    # result = create_document("Test Title", "# Hello\nThis is a test.")
    # print(result)
