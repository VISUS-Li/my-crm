#!/usr/bin/env python3
"""Compile CRM zh.po to sites/assets/locale/zh/LC_MESSAGES/crm.mo.

Uses Babel directly so Docker image build does not need an installed site or
importable crm package (bench compile-po-to-mo spawns workers that import crm).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

LOCALE = "zh"
APP = "crm"


def main() -> int:
	bench_dir = Path(os.environ.get("BENCH_DIR", Path.cwd())).resolve()
	po_path = bench_dir / "apps" / APP / APP / "locale" / f"{LOCALE}.po"
	mo_path = bench_dir / "sites" / "assets" / "locale" / LOCALE / "LC_MESSAGES" / f"{APP}.mo"

	if not po_path.is_file():
		print(f"ERROR: PO file not found: {po_path}", file=sys.stderr)
		return 1

	try:
		from babel.messages.mofile import write_mo
		from babel.messages.pofile import read_po
	except ImportError:
		print("ERROR: babel is required (use bench venv: ./env/bin/python)", file=sys.stderr)
		return 1

	mo_path.parent.mkdir(parents=True, exist_ok=True)
	with po_path.open("rb") as po_file:
		catalog = read_po(po_file)
	with mo_path.open("wb") as mo_file:
		write_mo(mo_file, catalog)

	print(f"Wrote {mo_path} ({mo_path.stat().st_size} bytes) from {po_path}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
