
## Exact failure from deployment `a3347fd2`

The Deploy Logs show that the workflow bypass advanced past the previous `validate_workflow()` issue. The current failure is a MySQL error while inserting the CRM module definition:

`MySQLdb.ProgrammingError: (1146, "Table '...tabModule Def' doesn't exist")`

The failing SQL is an `INSERT INTO tabModule Def (...) VALUES (...)` for module `FCRM`. This means the persistent site has an incomplete Frappe core schema: the `Module Def` table itself was never synchronized. The next repair must run the Frappe core schema synchronization/migration against the existing site before retrying `install-app crm`; it must not drop or recreate the site.
