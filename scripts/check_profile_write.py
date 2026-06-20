"""Non-destructive validation of v1.1 profile WRITE on the current X API tier.

This answers the project's biggest open technical question: does
account/update_profile (v1.1) work in our pay-per-use tier? It runs against the
MAIN account (whose OAuth 1.0a tokens we already have), and ALWAYS restores the
original name + bio afterwards (finally block), so nothing is left changed.

Run from the repo root, with Doppler injecting secrets:

    doppler run -- python scripts/check_profile_write.py

If this prints PASS, the Persona Dresser will work once personas are authorized.
If it prints a tier/permission error, we switch to Plan B (manual profile setup).
"""

from __future__ import annotations

import sys
import time

from finding_memeland.config import get_settings
from finding_memeland.social.x_client import XClient

# Plain alphanumerics only — X rejects some punctuation in bios (error 120).
TEST_BIO_MARKER = " fmmlselftest"


def main() -> int:
    s = get_settings()
    missing = [
        n
        for n, v in {
            "X_API_KEY": s.x_api_key,
            "X_API_SECRET": s.x_api_secret,
            "X_MAIN_ACCESS_TOKEN": s.x_main_access_token,
            "X_MAIN_ACCESS_SECRET": s.x_main_access_secret,
        }.items()
        if not v
    ]
    if missing:
        print(f"FAIL — missing secrets (is Doppler injecting?): {', '.join(missing)}")
        return 2

    x = XClient(api_key=s.x_api_key, api_secret=s.x_api_secret)
    tok, sec = s.x_main_access_token, s.x_main_access_secret

    # 1. Capture the real current profile.
    try:
        original = x.get_profile(tok, sec)
    except Exception as e:  # noqa: BLE001
        print(f"FAIL — could not read profile (auth/tier issue): {e!r}")
        return 1
    print(f"read OK  @{original.screen_name}  name={original.name!r}")

    # 2. Attempt a tiny, reversible write to the bio.
    test_bio = (original.description + TEST_BIO_MARKER)[:160]
    try:
        try:
            after = x.update_profile(tok, sec, description=test_bio)
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            if "120" in msg or "invalid characters" in msg.lower():
                # Endpoint works; X rejected the test content, not our access tier.
                print(f"PARTIAL — endpoint reachable, but X rejected the bio content: {e!r}")
                print("          The v1.1 write path IS available; sanitize bio chars.")
                return 3
            print(f"FAIL — update_profile rejected on this tier: {e!r}")
            print("       -> switch to Plan B: manual profile setup (keeps integrity hash).")
            return 1

        if TEST_BIO_MARKER.strip() in after.description:
            print("PASS — v1.1 update_profile WORKS on this tier. Dresser path is viable.")
            result = 0
        else:
            print(f"FAIL — write returned but did not take. bio={after.description!r}")
            result = 1
    finally:
        # 3. Always restore the original bio.
        time.sleep(1)
        try:
            x.update_profile(tok, sec, description=original.description)
            restored = x.get_profile(tok, sec)
            ok = restored.description == original.description
            print(f"restore {'OK' if ok else 'CHECK MANUALLY'}  bio={restored.description!r}")
        except Exception as e:  # noqa: BLE001
            print(f"WARNING — could not restore bio, set it back manually: {e!r}")
            print(f"          original bio was: {original.description!r}")

    return result


if __name__ == "__main__":
    sys.exit(main())
