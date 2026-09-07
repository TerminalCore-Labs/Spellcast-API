#!/usr/bin/env bash
#
# Clone the production Supabase database into a development one (TCORE-113).
#
# One-off / rare use: standing up a fresh dev DB, disaster recovery, or onboarding
# a new machine. Dev is local — there is no deployed staging.
#
# What it does:
#   1. pg_dump prod: the app schemas + data (no owners, no privileges)
#   2. restore into dev (drops & recreates the dumped objects)
#   3. re-grant the `accounts` schema to the Supabase API roles (dev_provision.sql),
#      which step 1 stripped via --no-privileges
#
# What it does NOT do (manual — see dev_utils/DEV_DATABASE.md):
#   - Expose the `accounts` schema in the dev project's PostgREST
#     (Dashboard > Settings > API > Exposed schemas: add `accounts`).
#     Supabase does not carry this in a dump and setting it via SQL is unreliable.
#   - Set VITE_DUMMY_ID (Spellcast-Client/.env) to a user id that exists in dev.
#
# Requires a PostgreSQL client >= the server major version. Supabase runs PG15+;
# Ubuntu 22.04 ships 14, so install postgresql-client-17. This script auto-prefers
# /usr/lib/postgresql/17/bin if present.
#
# Usage:
#   PROD_URL='postgresql://postgres.<ref-prod>:<pw>@<pooler-host>:5432/postgres' \
#   DEV_URL='postgresql://postgres.<ref-dev>:<pw>@<pooler-host>:5432/postgres' \
#   ./dev_utils/clone_prod_to_dev.sh
#
set -euo pipefail

: "${PROD_URL:?set PROD_URL to the production pooler connection string}"
: "${DEV_URL:?set DEV_URL to the development pooler connection string}"

# Prefer a modern client if the default (Ubuntu wrapper) is too old for the server.
if [ -x /usr/lib/postgresql/17/bin/pg_dump ]; then
  export PATH="/usr/lib/postgresql/17/bin:$PATH"
fi

# Guardrail: the pooler host is shared across projects in a region, so the project
# is identified by the user (postgres.<ref>). Refuse to run if prod and dev resolve
# to the same project — otherwise --clean would clobber production.
prod_ref=$(sed -E 's|^[a-z]+://([^:@]+).*|\1|' <<<"$PROD_URL")
dev_ref=$(sed -E 's|^[a-z]+://([^:@]+).*|\1|' <<<"$DEV_URL")
if [ "$prod_ref" = "$dev_ref" ]; then
  echo "ABORT: PROD_URL and DEV_URL resolve to the same project ($prod_ref)." >&2
  exit 1
fi

# App-owned schemas. Never dump Supabase-managed schemas (auth, storage, realtime,
# extensions, graphql, ...): they already exist in the dev project and overwriting
# them breaks it.
SCHEMAS=(accounts public spellcast spectra streamby havenstore)
SCHEMA_FLAGS=()
for s in "${SCHEMAS[@]}"; do SCHEMA_FLAGS+=(--schema="$s"); done

here="$(cd "$(dirname "$0")" && pwd)"
dump="$(mktemp "/tmp/prod_dump_$(date +%Y%m%d_%H%M%S)_XXXX.sql")"

echo "==> pg_dump version: $(pg_dump --version)"
echo "==> Dumping prod [$prod_ref]: ${SCHEMAS[*]}"
pg_dump "$PROD_URL" "${SCHEMA_FLAGS[@]}" \
  --no-owner --no-privileges --clean --if-exists -f "$dump"

echo "==> Restoring into dev [$dev_ref]"
# ON_ERROR_STOP=0: tolerate the harmless "does not exist, skipping" from DROP IF EXISTS.
psql "$DEV_URL" -v ON_ERROR_STOP=0 -f "$dump"

echo "==> Re-granting the accounts schema to the API roles"
psql "$DEV_URL" -v ON_ERROR_STOP=1 -f "$here/dev_provision.sql"

cat <<EOF

Done. Two manual steps remain in the DEV project (see dev_utils/DEV_DATABASE.md):
  1. Dashboard > Settings > API > Exposed schemas: add 'accounts'.
  2. Point VITE_DUMMY_ID (Spellcast-Client/.env) at a user that exists in dev:
       psql "\$DEV_URL" -c 'select id, email from accounts.users;'
EOF
