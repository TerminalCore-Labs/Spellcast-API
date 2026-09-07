# Development database (TCORE-113)

Dev runs **locally**: the APIs are started on the developer's machine against a
**separate Supabase project** whose data is cloned from production. There is no
deployed staging — Fly.io is production only.

The clone is a **rare, one-off operation** (fresh dev DB, disaster recovery, or a
new machine). It is not automated on a schedule; `clone_prod_to_dev.sh` just makes
the manual procedure repeatable instead of rediscovered each time.

## Why this is not trivial

`Spellcast-API` does **not** own the users table. `app/models/user.py` *reflects*
`accounts.users` (`autoload_with=engine`) — a table in the **`accounts` schema that
belongs to Nhexa**. Spellcast only points foreign keys at it. Consequences:

- The app **fails to import** (not just fails a request) if `accounts.users` does
  not exist — `sqlalchemy.exc.NoSuchTableError: users`. So the schema must be
  present *before* the API starts.
- `accounts` is read by **Nhexa-API through supabase-js → PostgREST**, so it needs
  to be **exposed** in the project's API settings and **granted** to the API roles.
  Neither the exposure nor (with `--no-privileges`) the grants travel in a dump.

## Procedure

### 0. Prerequisites

A PostgreSQL client **>= the server major version**. Supabase runs PG15+; Ubuntu
22.04 ships 14 (too old — `pg_dump` refuses). Install the modern client:

```bash
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh   # Enter to accept
sudo apt install -y postgresql-client-17
```

Connection strings: each project's **Session pooler** URI, from
Dashboard > Project Settings > Database. Passwords with special chars: wrap the
whole URI in **single quotes** (bash history-expands `!` inside double quotes).

### 1. Clone (schemas + data + accounts grants)

```bash
PROD_URL='postgresql://postgres.<ref-prod>:<pw>@<pooler>:5432/postgres' \
DEV_URL='postgresql://postgres.<ref-dev>:<pw>@<pooler>:5432/postgres' \
./dev_utils/clone_prod_to_dev.sh
```

The script dumps six app schemas — `accounts public spellcast spectra streamby
havenstore` — restores them into dev, and re-applies `dev_provision.sql`. It never
touches Supabase-managed schemas (`auth`, `storage`, ...), and aborts if PROD and
DEV resolve to the same project.

### 2. Expose `accounts` in PostgREST (manual, one field)

Dashboard (dev project) > **Settings > API > Exposed schemas** → add **`accounts`**
next to `public, graphql_public` → Save. Doing this via SQL
(`ALTER ROLE authenticator ...`) is unreliable on hosted Supabase; use the UI.

### 3. Point the dev login at a real user (manual)

`Spellcast-Client` logs in for local dev by POSTing a fixed user id
(`VITE_DUMMY_ID`) to Nhexa-API's `/dev/account`. Set it to a user that exists in
the cloned dev DB:

```bash
psql "$DEV_URL" -c 'select id, email from accounts.users;'
# put one id into Spellcast-Client/.env as VITE_DUMMY_ID, then restart the client
```

`Nhexa-API`'s `SUPABASE_URL` / `SUPABASE_KEY` must be the **dev** project's, and the
key must be the **service_role / secret** one (it bypasses RLS on `accounts.users`).

## Gotchas seen in the wild

| Symptom | Cause | Fix |
|---|---|---|
| `NoSuchTableError: users` on boot | `accounts.users` missing in dev | run the clone (step 1) |
| PostgREST `PGRST106` schema not exposed | `accounts` not in Exposed schemas | step 2 |
| `permission denied for schema accounts` (`42501`) | `--no-privileges` stripped grants | `dev_provision.sql` (in the script) |
| `pg_dump: aborting because of server version mismatch` | client older than server | install `postgresql-client-17` |
| `/dev/account` 404 loop | `VITE_DUMMY_ID` not a user in dev, or Nhexa-API on the wrong key/project | step 3 |

## Fernet key after a prod rotation

`spellcast.credential.config` is encrypted with the prod Fernet key. Dev keeps its
own (older) key on purpose. If you **re-clone** prod into dev *after* prod's Fernet
key was rotated (see `dev_utils/rotate_fernet_key.py`), the cloned rows are now
encrypted with the **new** prod key, which dev's `.env` does not have — decryption
in dev will fail. When that happens, either put the new key in the dev `.env` too,
or scrub the table: `delete from spellcast.credential;` (dev only).
