#!/usr/bin/env python3
"""Sync local CRM code to Ubuntu server and optionally build + restart.

Usage (from repo root on Windows):
  python scripts/sync_to_server.py              # sync only
  python scripts/sync_to_server.py --deploy     # sync + build + restart
  python scripts/sync_to_server.py --setup-key  # copy SSH public key to server

Config: scripts/deploy.config.json (copy from deploy.config.example.json)
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import stat
import sys
from pathlib import Path

try:
    import paramiko
except ImportError:
    print("Installing paramiko...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(__file__).resolve().parent / "deploy.config.json"
EXAMPLE_CONFIG = Path(__file__).resolve().parent / "deploy.config.example.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        if EXAMPLE_CONFIG.exists():
            import shutil

            shutil.copy(EXAMPLE_CONFIG, CONFIG_PATH)
            print(f"Created {CONFIG_PATH} — edit password if not using SSH key.")
        else:
            sys.exit(f"Missing config: {CONFIG_PATH}")
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def should_exclude(rel_path: str, exclude_patterns: list[str]) -> bool:
    parts = rel_path.replace("\\", "/").split("/")
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(rel_path.replace("\\", "/"), pattern):
            return True
        if any(fnmatch.fnmatch(part, pattern) for part in parts):
            return True
    return False


def iter_local_files(root: Path, exclude_patterns: list[str]):
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root).as_posix()
        if rel_dir != "." and should_exclude(rel_dir, exclude_patterns):
            dirnames.clear()
            continue
        dirnames[:] = [
            d
            for d in dirnames
            if not should_exclude(
                f"{rel_dir}/{d}" if rel_dir != "." else d, exclude_patterns
            )
        ]
        for name in filenames:
            rel = f"{rel_dir}/{name}" if rel_dir != "." else name
            if not should_exclude(rel, exclude_patterns):
                yield rel, Path(dirpath) / name


def connect(cfg: dict) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs = {
        "hostname": cfg["host"],
        "username": cfg["user"],
        "port": cfg.get("port", 22),
        "timeout": 30,
    }
    password = cfg.get("password") or None
    key_path = Path.home() / ".ssh" / "id_ed25519"
    if key_path.exists():
        kwargs["key_filename"] = str(key_path)
    if password:
        kwargs["password"] = password
    client.connect(**kwargs)
    return client


def setup_ssh_key(cfg: dict) -> None:
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    key_path = ssh_dir / "id_ed25519"
    pub_path = ssh_dir / "id_ed25519.pub"

    if not key_path.exists():
        print("Generating SSH key...")
        import subprocess

        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-f", str(key_path), "-N", ""],
            check=True,
        )

    pub_key = pub_path.read_text(encoding="utf-8").strip()
    client = connect(cfg)
    cmd = (
        f"mkdir -p ~/.ssh && chmod 700 ~/.ssh && "
        f"grep -qxF '{pub_key}' ~/.ssh/authorized_keys 2>/dev/null || "
        f"echo '{pub_key}' >> ~/.ssh/authorized_keys && "
        f"chmod 600 ~/.ssh/authorized_keys"
    )
    _, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    err = stderr.read().decode()
    if err and "grep" not in err:
        print(err)
    client.close()
    print("SSH key installed. You can remove password from deploy.config.json.")


def ensure_remote_dir_sftp(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    remote_dir = remote_dir.replace("\\", "/")
    if remote_dir in ("", "/"):
        return
    try:
        sftp.stat(remote_dir)
        return
    except FileNotFoundError:
        parent = os.path.dirname(remote_dir)
        if parent and parent != remote_dir:
            ensure_remote_dir_sftp(sftp, parent)
        sftp.mkdir(remote_dir)


def sync_files(cfg: dict) -> int:
    remote_root = cfg["remote_crm_src"]
    exclude = cfg.get("exclude", [])
    client = connect(cfg)
    sftp = client.open_sftp()

    uploaded = 0
    for rel, local_path in iter_local_files(REPO_ROOT, exclude):
        remote_path = f"{remote_root}/{rel.replace(chr(92), '/')}"
        remote_dir = os.path.dirname(remote_path).replace("\\", "/")
        ensure_remote_dir_sftp(sftp, remote_dir)

        local_mtime = local_path.stat().st_mtime
        try:
            remote_stat = sftp.stat(remote_path)
            if remote_stat.st_mtime >= local_mtime and remote_stat.st_size == local_path.stat().st_size:
                continue
        except FileNotFoundError:
            pass

        sftp.put(str(local_path), remote_path)
        sftp.chmod(remote_path, local_path.stat().st_mode & 0o777)
        uploaded += 1

    sftp.close()
    client.close()
    print(f"Synced {uploaded} changed file(s) to {remote_root}")
    return uploaded


def run_remote_deploy(cfg: dict) -> None:
    remote_root = cfg["remote_crm_src"]
    cmd = f"bash {remote_root}/scripts/deploy-remote.sh"
    client = connect(cfg)
    print("==> Running deploy on server...")
    _, stdout, stderr = client.exec_command(cmd, get_pty=True)
    for line in iter(stdout.readline, ""):
        sys.stdout.buffer.write(line.encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()
    exit_code = stdout.channel.recv_exit_status()
    err = stderr.read().decode()
    if err:
        sys.stderr.write(err)
    client.close()
    if exit_code != 0:
        sys.exit(f"Deploy failed with exit code {exit_code}")


def ensure_remote_dir(cfg: dict) -> None:
    client = connect(cfg)
    remote_root = cfg["remote_crm_src"]
    client.exec_command(f"mkdir -p {remote_root}")
    client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync CRM code to Ubuntu server")
    parser.add_argument("--deploy", action="store_true", help="Build frontend and restart bench after sync")
    parser.add_argument("--setup-key", action="store_true", help="Install local SSH public key on server")
    args = parser.parse_args()

    cfg = load_config()

    if args.setup_key:
        setup_ssh_key(cfg)
        return

    ensure_remote_dir(cfg)
    sync_files(cfg)

    if args.deploy:
        run_remote_deploy(cfg)


if __name__ == "__main__":
    main()
