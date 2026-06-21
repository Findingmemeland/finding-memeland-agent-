"""Round-trip test against the real Supabase project.

Inserts a throwaway hunt row, reads it back, then deletes it — confirming the
service-role key, schema and Repo all line up. No game state is left behind.

Prerequisites in .env:
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY   (the sb_secret_... key)

    python scripts/test_supabase.py
"""

from __future__ import annotations

import sys

from finding_memeland.config import get_settings
from finding_memeland.db.client import Repo, make_client


def main() -> int:
    s = get_settings()
    if not s.supabase_url or not s.supabase_service_role_key:
        print("FAIL — set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env.")
        return 2

    client = make_client(s.supabase_url, s.supabase_service_role_key)
    repo = Repo(client)

    print("inserting a test hunt...")
    hunt_id = repo.create_hunt(
        claim_code="TESTCODE",
        integrity_salt="testsalt",
        integrity_hash="0" * 64,
        holding_hours=48,
        state="preparing",
    )
    print(f"PASS — created hunt id={hunt_id}")

    repo.set_hunt_state(hunt_id, "voided")
    back = client.table("hunts").select("*").eq("id", hunt_id).execute()
    row = (back.data or [{}])[0]
    print(f"read back: state={row.get('state')} claim_code={row.get('claim_code')}")

    # clean up
    client.table("hunts").delete().eq("id", hunt_id).execute()
    gone = client.table("hunts").select("id").eq("id", hunt_id).execute()
    ok = not gone.data
    print(f"cleanup {'OK' if ok else 'FAILED'} — test hunt deleted")

    success = row.get("state") == "voided" and ok
    print("\nALL GOOD — Supabase repo works." if success else "\nsomething off, check above.")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
