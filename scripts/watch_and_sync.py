#!/usr/bin/env python3
"""Watch local files and auto-sync + deploy to Ubuntu server.

Usage:
  python scripts/watch_and_sync.py
  python scripts/watch_and_sync.py --interval 5   # debounce seconds
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC_SCRIPT = Path(__file__).resolve().parent / "sync_to_server.py"


def get_mtime_snapshot(root: Path, exclude_dirs: set[str]) -> dict[str, float]:
    mtimes: dict[str, float] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in exclude_dirs for part in rel.parts):
            continue
        if "node_modules" in rel.parts or ".git" in rel.parts:
            continue
        mtimes[str(rel)] = path.stat().st_mtime
    return mtimes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=3.0, help="Debounce seconds after last change")
    args = parser.parse_args()

    exclude = {".git", "node_modules", ".pi", "dev-dist", "build", "coverage"}
    print(f"Watching {REPO_ROOT} — changes sync + deploy after {args.interval}s idle")
    print("Press Ctrl+C to stop.")

    snapshot = get_mtime_snapshot(REPO_ROOT, exclude)
    pending = False
    last_change = 0.0

    try:
        while True:
            time.sleep(1)
            current = get_mtime_snapshot(REPO_ROOT, exclude)
            if current != snapshot:
                snapshot = current
                pending = True
                last_change = time.time()
                print(".", end="", flush=True)

            if pending and (time.time() - last_change) >= args.interval:
                print("\n==> Syncing and deploying...")
                result = subprocess.run(
                    [sys.executable, str(SYNC_SCRIPT), "--deploy"],
                    cwd=REPO_ROOT,
                )
                if result.returncode != 0:
                    print("Deploy failed.", file=sys.stderr)
                pending = False
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
