#!/usr/bin/env python3
"""Apply TripAI connection settings on the remote CRM server from deploy.config.json.

Usage (from repo root):
  python scripts/configure_tripai.py
  python scripts/configure_tripai.py --base-url http://10.0.160.64:3000
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import paramiko
except ImportError:
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

CONFIG_PATH = Path(__file__).resolve().parent / "deploy.config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"Missing {CONFIG_PATH}")
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def connect(cfg: dict) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs = {
        "hostname": cfg["host"],
        "username": cfg["user"],
        "port": cfg.get("port", 22),
        "timeout": 30,
    }
    key_path = Path.home() / ".ssh" / "id_ed25519"
    if key_path.exists():
        kwargs["key_filename"] = str(key_path)
    password = cfg.get("password") or None
    if password:
        kwargs["password"] = password
    client.connect(**kwargs)
    return client


def main() -> None:
    parser = argparse.ArgumentParser(description="Configure TripAI base URL on remote CRM server")
    parser.add_argument("--base-url", help="TripAI base URL (overrides deploy.config.json)")
    parser.add_argument("--enabled", type=int, default=1, choices=(0, 1))
    parser.add_argument("--project-key")
    parser.add_argument("--tool-key")
    parser.add_argument("--test", action="store_true", help="Run test_connection after apply")
    args = parser.parse_args()

    cfg = load_config()
    base_url = (args.base_url or cfg.get("tripai_base_url") or "").strip()
    if not base_url:
        sys.exit("Set tripai_base_url in deploy.config.json or pass --base-url")

    kwargs = {
        "base_url": base_url,
        "enabled": args.enabled,
    }
    project_key = args.project_key or cfg.get("tripai_project_key")
    tool_key = args.tool_key or cfg.get("tripai_tool_key")
    if project_key:
        kwargs["project_key"] = project_key
    if tool_key:
        kwargs["tool_key"] = tool_key

    site_name = cfg.get("site_name", "crm.localhost")
    bench_dir = cfg.get("remote_bench", "$HOME/frappe-bench")
    kwargs_json = json.dumps(kwargs, ensure_ascii=False)

    apply_cmd = (
        f"export PATH=$HOME/.local/bin:$PATH && "
        f"cd {bench_dir} && "
        f"bench --site {site_name} execute crm.integrations.tripai.configure.apply_connection_settings "
        f"--kwargs '{kwargs_json}'"
    )

    client = connect(cfg)
    print(f"==> Applying TripAI settings: {kwargs}")
    _, stdout, stderr = client.exec_command(apply_cmd)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(out.strip())
    if err:
        print(err.strip(), file=sys.stderr)
    if exit_code != 0:
        client.close()
        sys.exit(f"Failed with exit code {exit_code}")

    if args.test:
        test_cmd = (
            f"export PATH=$HOME/.local/bin:$PATH && "
            f"cd {bench_dir} && "
            f"bench --site {site_name} execute crm.api.tripai.test_connection"
        )
        print("==> Testing TripAI connection from CRM server...")
        _, stdout, stderr = client.exec_command(test_cmd)
        stdout.channel.recv_exit_status()
        print(stdout.read().decode().strip())
        err = stderr.read().decode().strip()
        if err:
            print(err, file=sys.stderr)

    client.close()
    print("Done.")


if __name__ == "__main__":
    main()
