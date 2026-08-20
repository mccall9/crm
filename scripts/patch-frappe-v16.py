#!/usr/bin/env python3
"""Apply narrow, idempotent compatibility fixes to the Frappe v16 runtime.

The CRM develop branch currently uses DocType metadata fields that the
version-16 Frappe branch accesses without defaults while installing special
DocTypes. These changes are applied inside the generated Bench only; the CRM
source tree is not modified.
"""
from __future__ import annotations

import sys
from pathlib import Path


OPTIONAL_FIELDS = {
    "options",
    "parent",
    "parentfield",
    "parenttype",
    "title_field",
    "istable",
    "ignore_user_permissions",
}


BASE_DOCUMENT_FALLBACK = '''\n\tdef __getattr__(self, key):\n\t\tif key in OPTIONAL_FIELDS:\n\t\t\treturn None\n\t\traise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")\n'''


def replace_all(path: Path, replacements: list[tuple[str, str]]) -> None:
    text = path.read_text()
    updated = text
    for old, new in replacements:
        updated = updated.replace(old, new)
    if updated != text:
        path.write_text(updated)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch-frappe-v16.py BENCH_DIR", file=sys.stderr)
        return 2

    bench_dir = Path(sys.argv[1])
    frappe_dir = bench_dir / "apps" / "frappe" / "frappe"
    if not frappe_dir.is_dir():
        print(f"Frappe source not found at {frappe_dir}", file=sys.stderr)
        return 1

    meta = frappe_dir / "model" / "meta.py"
    if meta.exists():
        replace_all(meta, [("self.istable", 'getattr(self, "istable", False)')])

    create_new = frappe_dir / "model" / "create_new.py"
    if create_new.exists():
        replace_all(
            create_new,
            [
                ("df.options", 'getattr(df, "options", None)'),
                ("df.parent", 'getattr(df, "parent", None)'),
                ("doc.meta.title_field", 'getattr(doc.meta, "title_field", None)'),
            ],
        )

    base_document = frappe_dir / "model" / "base_document.py"
    if base_document.exists() and "def __getattr__(self, key)" not in base_document.read_text():
        text = base_document.read_text()
        marker = "class BaseDocument:\n"
        if marker in text:
            text = text.replace(marker, marker + BASE_DOCUMENT_FALLBACK, 1)
            text = text.replace(
                "class BaseDocument:\n",
                "class BaseDocument:\n",
                1,
            )
            # Keep the optional-field set close to the fallback without
            # introducing imports or touching application code.
            text = text.replace(
                "class BaseDocument:\n",
                "class BaseDocument:\n\tOPTIONAL_FIELDS = " + repr(OPTIONAL_FIELDS) + "\n",
                1,
            )
            text = text.replace(
                "if key in OPTIONAL_FIELDS:",
                "if key in self.OPTIONAL_FIELDS:",
                1,
            )
            base_document.write_text(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
