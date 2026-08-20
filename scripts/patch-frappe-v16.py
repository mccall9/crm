#!/usr/bin/env python3
"""Apply narrow, idempotent compatibility fixes to the generated Frappe v16 Bench.

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
    "is_submittable",
}

BASE_DOCUMENT_FALLBACK = (
    "\n\tdef __getattr__(self, key):"
    "\n\t\tif key in self.OPTIONAL_FIELDS:"
    "\n\t\t\treturn None"
    "\n\t\traise AttributeError(f\"'{type(self).__name__}' object has no attribute '{key}'\")"
    "\n"
)


def replace_all(path: Path, replacements: list[tuple[str, str]]) -> None:
    text = path.read_text()
    updated = text
    for old, new in replacements:
        updated = updated.replace(old, new)
    if updated != text:
        path.write_text(updated)


def patch_base_document(path: Path) -> None:
    text = path.read_text()
    class_marker = "class BaseDocument:\n"
    if class_marker not in text:
        return

    attr_line = "\tOPTIONAL_FIELDS = " + repr(OPTIONAL_FIELDS)
    lines = text.splitlines(keepends=True)
    attr_index = next((i for i, line in enumerate(lines) if "OPTIONAL_FIELDS =" in line), None)
    if attr_index is None:
        insert_at = next(i for i, line in enumerate(lines) if line == class_marker) + 1
        lines.insert(insert_at, attr_line + "\n")
        text = "".join(lines)
    else:
        line = lines[attr_index]
        newline = "\n" if line.endswith("\n") else ""
        lines[attr_index] = attr_line + newline
        text = "".join(lines)

    if "def __getattr__(self, key)" not in text:
        text = text.replace(class_marker, class_marker + BASE_DOCUMENT_FALLBACK, 1)
    else:
        text = text.replace("if key in OPTIONAL_FIELDS:", "if key in self.OPTIONAL_FIELDS:")

    path.write_text(text)


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
        replace_all(
            meta,
            [
                ("self.istable", 'getattr(self, "istable", False)'),
                (
                    "if (frappe.flags.in_install or frappe.flags.in_migrate) and self.name in self.special_doctypes:",
                    "if (frappe.flags.in_install or frappe.flags.in_migrate) and self.name in self.special_doctypes and frappe.db.table_exists(self.name):",
                ),
            ],
        )

    document = frappe_dir / "model" / "document.py"
    if document.exists():
        replace_all(
            document,
            [
                (
                    'if frappe.flags.in_install == "frappe":\n\t\t\treturn',
                    'if frappe.flags.in_install == "frappe" or (frappe.flags.in_install and not frappe.db.table_exists("Workflow")):\n\t\t\treturn',
                ),
            ],
        )

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
    if base_document.exists():
        patch_base_document(base_document)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
