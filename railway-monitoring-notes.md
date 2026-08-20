
## New failure in deployment `292cd0e1`

The new bootstrap reached the migration stage but `bench --site ... migrate` failed because the partial site also lacks `tabPatch Log`. Railway logs show `frappe.database.database.TableMissingError: ('DocType', 'Patch Log')` from `frappe.model.meta.get_table_columns()` while the patch handler queried Patch Log. This confirms the site is missing multiple core tables, not just `Module Def`.

The service was still marked `Deploying` at the time of capture, with MySQL and Redis online. The next non-destructive repair should invoke the Frappe core DocType synchronizer directly before `migrate`, so it can create missing core tables such as `Patch Log` and `Module Def`; no site deletion or recreation is permitted.
