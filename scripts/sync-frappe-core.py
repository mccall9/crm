#!/usr/bin/env python3
"""Synchronize Frappe's core DocTypes on an existing site without recreating it."""

from __future__ import annotations

import sys

import frappe
from frappe.model.sync import sync_for


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: sync-frappe-core.py SITE_NAME SITES_PATH")

    site_name, sites_path = sys.argv[1:]
    frappe.init(site=site_name, sites_path=sites_path)
    try:
        frappe.connect()
        # The site may not yet have Workflow while core DocTypes are restored.
        # Mark this as a Frappe installation sync so the compatibility guard
        # skips workflow validation until the core schema is complete.
        frappe.flags.in_install = "frappe"
        frappe.flags.in_migrate = True
        sync_for("frappe")
        frappe.db.commit()
    finally:
        frappe.destroy()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
