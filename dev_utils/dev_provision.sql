-- Dev database provisioning — grants that `pg_dump --no-privileges` strips (TCORE-113).
--
-- clone_prod_to_dev.sh dumps the schemas + data with --no-privileges (to avoid
-- cross-project role/ownership noise), which also drops every GRANT. The Supabase
-- API roles then lose access to the custom `accounts` schema, and PostgREST fails
-- with: "permission denied for schema accounts" (SQLSTATE 42501).
--
-- `accounts.users` is Nhexa's identity table, read by Nhexa-API through supabase-js
-- (PostgREST) with the service_role key. service_role bypasses RLS but still needs
-- USAGE on the schema — that is what these grants restore. RLS policies themselves
-- ARE carried by the dump, so row-level access stays as in production.
--
-- Only `accounts` needs this: every other schema (spellcast, streamby, havenstore,
-- spectra) is reached over a direct SQL connection as the owner role, not PostgREST.

grant usage on schema accounts to anon, authenticated, service_role;
grant select, insert, update, delete on all tables in schema accounts to anon, authenticated, service_role;
grant usage, select on all sequences in schema accounts to anon, authenticated, service_role;
