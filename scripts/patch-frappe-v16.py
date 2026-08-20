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


SEQUENCE_COMPATIBILITY = r'''

# MANUS_MYSQL_SEQUENCE_COMPAT
_MANUS_SEQUENCE_TABLE = "`__frappe_sequence`"
_MANUS_SEQUENCE_READY = False


def _manus_ensure_mysql_sequence_store():
\tglobal _MANUS_SEQUENCE_READY
\tif _MANUS_SEQUENCE_READY:
\t\treturn
\tdb.sql_ddl(
\t\t"CREATE TABLE IF NOT EXISTS `__frappe_sequence` "
\t\t"(`name` varchar(140) NOT NULL, `current` bigint NOT NULL, "
\t\t"PRIMARY KEY (`name`)) ENGINE=InnoDB"
\t)
\t_MANUS_SEQUENCE_READY = True


_MANUS_NATIVE_CREATE_SEQUENCE = create_sequence
_MANUS_NATIVE_GET_NEXT_VAL = get_next_val
_MANUS_NATIVE_SET_NEXT_VAL = set_next_val


def create_sequence(
\tdoctype_name: str,
\t*,
\tslug: str = "_id_seq",
\ttemporary: bool = False,
\tcheck_not_exists: bool = False,
\tcycle: bool = False,
\tcache: int = SEQUENCE_CACHE,
\tstart_value: int = 0,
\tincrement_by: int = 0,
\tmin_value: int = 0,
\tmax_value: int = 0,
) -> str:
\tif db.db_type != "mariadb":
\t\treturn _MANUS_NATIVE_CREATE_SEQUENCE(
\t\t\tdoctype_name,
\t\t\tslug=slug,
\t\t\ttemporary=temporary,
\t\t\tcheck_not_exists=check_not_exists,
\t\t\tcycle=cycle,
\t\t\tcache=cache,
\t\t\tstart_value=start_value,
\t\t\tincrement_by=increment_by,
\t\t\tmin_value=min_value,
\t\t\tmax_value=max_value,
\t\t)

\t_manus_ensure_mysql_sequence_store()
\tsequence_name = scrub(doctype_name + slug)
\tinitial_value = start_value - 1 if start_value else 0
\tdb.sql(
\t\t"INSERT IGNORE INTO `__frappe_sequence` (`name`, `current`) VALUES (%s, %s)",
\t\t(sequence_name, initial_value),
\t)
\treturn sequence_name


def get_next_val(doctype_name: str, slug: str = "_id_seq") -> int:
\tif db.db_type != "mariadb":
\t\treturn _MANUS_NATIVE_GET_NEXT_VAL(doctype_name, slug)

\t_manus_ensure_mysql_sequence_store()
\tsequence_name = scrub(f"{doctype_name}{slug}")
\tquery = (
\t\t"UPDATE `__frappe_sequence` "
\t\t"SET `current` = LAST_INSERT_ID(`current` + 1) "
\t\t"WHERE `name` = %s"
\t)
\tdb.sql(query, (sequence_name,))
\tif db.sql("SELECT ROW_COUNT()")[0][0] == 0:
\t\tcreate_sequence(doctype_name, slug=slug)
\t\tdb.sql(query, (sequence_name,))
\treturn int(db.sql("SELECT LAST_INSERT_ID()")[0][0])


def set_next_val(
\tdoctype_name: str, next_val: int, *, slug: str = "_id_seq", is_val_used: bool = False
) -> None:
\tif db.db_type != "mariadb":
\t\treturn _MANUS_NATIVE_SET_NEXT_VAL(
\t\t\tdoctype_name, next_val, slug=slug, is_val_used=is_val_used
\t\t)

\t_manus_ensure_mysql_sequence_store()
\tsequence_name = scrub(f"{doctype_name}{slug}")
\tcurrent_value = next_val if is_val_used else next_val - 1
\tdb.sql(
\t\t"INSERT INTO `__frappe_sequence` (`name`, `current`) VALUES (%s, %s) "
\t\t"ON DUPLICATE KEY UPDATE `current` = %s",
\t\t(sequence_name, current_value, current_value),
\t)
'''


def replace_all(path: Path, replacements: list[tuple[str, str]]) -> None:
    text = path.read_text()
    updated = text
    for old, new in replacements:
        updated = updated.replace(old, new)
    if updated != text:
        path.write_text(updated)


def patch_sequence(path: Path) -> None:
    text = path.read_text()
    if "# MANUS_MYSQL_SEQUENCE_COMPAT" in text:
        return
    compatibility = SEQUENCE_COMPATIBILITY.replace("\\t", "\t")
    path.write_text(text.rstrip() + compatibility + "\n")


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

    sequence = frappe_dir / "database" / "sequence.py"
    if sequence.exists():
        replace_all(
            sequence,
            [("\tif check_not_exists:\n\t\tquery += \" if not exists\"", "\tif check_not_exists and db.db_type != \"mariadb\":\n\t\tquery += \" if not exists\"")],
        )
        patch_sequence(sequence)

    mariadb_schema = frappe_dir / "database" / "mariadb" / "mysqlclient.py"
    if mariadb_schema.exists():
        replace_all(
            mariadb_schema,
            [("ADD INDEX IF NOT EXISTS", "ADD INDEX")],
        )

    schema = frappe_dir / "database" / "schema.py"
    if schema.exists():
        replace_all(
            schema,
            [
                (
                    '\t\telif (\n\t\t\tself.default\n\t\t\tand (self.default not in frappe.db.DEFAULT_SHORTCUTS)\n\t\t\tand not cstr(self.default).startswith(":")\n\t\t):\n\t\t\tdefault = frappe.db.escape(self.default)',
                    '\t\telif (\n\t\t\tself.default\n\t\t\tand (self.default not in frappe.db.DEFAULT_SHORTCUTS)\n\t\t\tand not cstr(self.default).startswith(":")\n\t\t):\n\t\t\t# MariaDB rejects defaults on TEXT/LONGTEXT/JSON columns.\n\t\t\tif column_def in ("text", "longtext", "json"):\n\t\t\t\tdefault = None\n\t\t\telse:\n\t\t\t\tdefault = frappe.db.escape(self.default)',
                ),
            ],
        )

    base_document = frappe_dir / "model" / "base_document.py"
    if base_document.exists():
        patch_base_document(base_document)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
