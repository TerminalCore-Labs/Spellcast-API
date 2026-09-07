#!/usr/bin/env python3
"""
Rotate the Fernet key that encrypts spellcast.credential.config (TCORE-115).

`spellcast.credential.config` is the ONLY Fernet-encrypted data in the app. This
one interactive script:

  1. prompts for the DATABASE_URL and the OLD (current) Fernet key, hidden;
  2. backs up spellcast.credential to a local .sql file (aborts if the dump fails);
  3. re-encrypts every row with a freshly generated key using MultiFernet.rotate
     (decrypt old / encrypt new), in a single all-or-nothing transaction;
  4. prints the NEW key.

The app builds Fernet(FERNET_KEY) from a single key, so the stored data and the
app's key must switch together. After this succeeds:

    fly secrets set FERNET_KEY='<new key>' -a api-spellcast   # then it redeploys

Do it in a low-traffic window (between the rotation and the redeploy, the data is
on the new key but the app still has the old one).

Run:  python3 dev_utils/rotate_fernet_key.py   (from the Spellcast-API directory)
Needs: cryptography + sqlalchemy + psycopg (app deps) + pg_dump (client >= server).
"""
import datetime
import getpass
import os
import subprocess
import sys

from cryptography.fernet import Fernet, MultiFernet, InvalidToken
from sqlalchemy import create_engine, text

TABLE = "spellcast.credential"


def main():
    print(f"Fernet key rotation for {TABLE}\n")
    raw_url = getpass.getpass("DATABASE_URL (hidden): ").strip()
    old_key = getpass.getpass("OLD Fernet key (current, hidden): ").strip()
    if not raw_url or not old_key:
        sys.exit("DATABASE_URL and OLD key are both required.")

    try:
        old_f = Fernet(old_key.encode())
    except Exception:
        sys.exit("OLD key is not a valid Fernet key.")

    # pg_dump needs a plain libpq URI; SQLAlchemy needs the psycopg (v3) driver.
    libpq_url = raw_url.replace("postgresql+psycopg://", "postgresql://")
    sa_url = libpq_url
    for prefix in ("postgresql://", "postgres://"):
        if sa_url.startswith(prefix):
            sa_url = "postgresql+psycopg://" + sa_url[len(prefix):]
            break

    # --- 1. backup first (never rotate without one) ---
    pg_dump = "/usr/lib/postgresql/17/bin/pg_dump"
    if not os.path.exists(pg_dump):
        pg_dump = "pg_dump"
    backup = f"credential_backup_{datetime.datetime.now():%Y%m%d_%H%M%S}.sql"
    print(f"Backing up {TABLE} -> {backup}")
    dump = subprocess.run(
        [pg_dump, libpq_url, "-t", TABLE, "--no-owner", "--no-privileges", "-f", backup]
    )
    if dump.returncode != 0:
        sys.exit("ABORT: backup failed — nothing was rotated.")
    print("Backup OK.\n")

    # --- 2. read + verify (no writes yet) ---
    new_key = Fernet.generate_key()
    mf = MultiFernet([Fernet(new_key), old_f])  # rotate() re-encrypts with the primary (new)
    engine = create_engine(sa_url)
    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT id, config FROM {TABLE}")).fetchall()

    print(f"Rows found: {len(rows)}")
    if rows:
        # verify-before-write: abort if the current key cannot decrypt existing data,
        # so a wrong OLD key can never corrupt the table.
        try:
            mf.decrypt(rows[0].config.encode())
        except InvalidToken:
            sys.exit("ABORT: the OLD key does not decrypt existing data. Wrong key?")

        if input(f"Re-encrypt {len(rows)} row(s)? Type 'yes' to proceed: ").strip() != "yes":
            sys.exit("Cancelled — nothing written (the backup is kept).")

        # --- 3. single transaction: all-or-nothing ---
        with engine.begin() as conn:
            for r in rows:
                rotated = mf.rotate(r.config.encode()).decode()
                conn.execute(
                    text(f"UPDATE {TABLE} SET config = :c WHERE id = :i"),
                    {"c": rotated, "i": r.id},
                )
        print(f"Re-encrypted {len(rows)} row(s).")
    else:
        print("No rows to re-encrypt (still generating a new key for the app).")

    print("\n" + "=" * 60)
    print("NEW Fernet key — set it in Fly and redeploy:\n")
    print("  " + new_key.decode())
    print("=" * 60)
    print(
        "\nNext:\n"
        "  fly secrets set FERNET_KEY='<the key above>' -a api-spellcast\n"
        "  (it redeploys) — the stored data is now on the new key, so the app must switch too.\n"
        f"  Keep {backup} until you've confirmed decryption works in prod.\n"
    )


if __name__ == "__main__":
    main()
