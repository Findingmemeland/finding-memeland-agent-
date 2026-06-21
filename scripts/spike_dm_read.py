"""Spike — can we READ DMs on the main account in our X API tier?

Answers the open question before we build the DM Listener (step 26): does the API
let us read inbound DMs with our keys, what does the data look like, and roughly
what does it cost. Uses OAuth 1.0a user context (the 4 main-account keys).

Tip: first send a test DM to @FindingMemeland from your personal X account, so
there's a real event to inspect. An empty inbox still confirms permission (the
call returns 200 with no data).

    python scripts/spike_dm_read.py
"""

from __future__ import annotations

import sys

import tweepy

from finding_memeland.config import get_settings


def main() -> int:
    s = get_settings()
    missing = [
        n for n, v in {
            "X_API_KEY": s.x_api_key, "X_API_SECRET": s.x_api_secret,
            "X_MAIN_ACCESS_TOKEN": s.x_main_access_token,
            "X_MAIN_ACCESS_SECRET": s.x_main_access_secret,
        }.items() if not v
    ]
    if missing:
        print(f"FAIL — missing in .env: {', '.join(missing)}")
        return 2

    client = tweepy.Client(
        consumer_key=s.x_api_key,
        consumer_secret=s.x_api_secret,
        access_token=s.x_main_access_token,
        access_token_secret=s.x_main_access_secret,
    )

    try:
        resp = client.get_direct_message_events(
            max_results=20,
            dm_event_fields=[
                "id", "text", "created_at", "sender_id",
                "event_type", "dm_conversation_id",
            ],
            expansions=["sender_id"],
            user_auth=True,
        )
    except Exception as e:  # noqa: BLE001
        print(f"FAIL — could not read DMs (permission/tier issue?): {e!r}")
        return 1

    events = resp.data or []
    users = {}
    if resp.includes and resp.includes.get("users"):
        users = {u.id: u for u in resp.includes["users"]}

    print(f"PASS — DM read call succeeded. {len(events)} event(s) returned.\n")
    if not events:
        print("Inbox empty — but the call worked, so DM-read permission/tier is confirmed.")
        return 0

    for ev in events:
        sender = users.get(getattr(ev, "sender_id", None))
        who = f"@{sender.username}" if sender else getattr(ev, "sender_id", "?")
        print(f"- id={ev.id} type={ev.event_type} from={who} at={ev.created_at}")
        text = getattr(ev, "text", None)
        if text:
            print(f"    text: {text}")
    print("\nThis is the shape the DM Listener (step 26) will parse.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
