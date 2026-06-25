"""Daily findability monitor — tracks when warmup accounts become searchable.

For each account in monitor_accounts.json, searches X recent tweets for that
account's distinctive phrase and records whether it surfaces yet. Appends a dated
line to findability_log.txt and fires a macOS notification with the summary.

Limitation: X recent-search only covers the last ~7 days. Keep a distinctive
recent tweet up on each account; if 7 days pass with no hit, post a NEW
distinctive tweet and update its phrase in monitor_accounts.json.

    python scripts/monitor_findability.py

Config (monitor_accounts.json, next to this repo root):
    [
      {"label": "10d email-only", "handle": "sarah_k392", "phrase": "the velvet hum of an unfinished atlas"},
      ...
    ]
"""

from __future__ import annotations

import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from finding_memeland.config import get_settings
from finding_memeland.social.x_client import XClient

CONFIG = Path("monitor_accounts.json")
LOG = Path("findability_log.txt")


def _notify(title: str, message: str) -> None:
    if platform.system() != "Darwin":
        return
    try:
        subprocess.run(
            ["osascript", "-e", f'display notification "{message}" with title "{title}"'],
            check=False,
        )
    except Exception:  # noqa: BLE001
        pass


def main() -> int:
    if not CONFIG.exists():
        print(f"FAIL — create {CONFIG} with [{{label, handle, phrase}}, ...].")
        return 2
    accounts = json.loads(CONFIG.read_text())

    s = get_settings()
    x = XClient(
        api_key=s.x_api_key, api_secret=s.x_api_secret,
        main_access_token=s.x_main_access_token, main_access_secret=s.x_main_access_secret,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines, findable = [], 0
    for acc in accounts:
        label, handle, phrase = acc["label"], acc["handle"], acc["phrase"]
        try:
            # Only the POST-CONTENT path (a clue-derivable phrase). NOT from:@handle —
            # the handle path is unusable (agent can't change handles) and we don't
            # want to depend on it.
            by_phrase = len(x.search_recent(f'"{phrase}"', max_results=10)) > 0
        except Exception as e:  # noqa: BLE001
            lines.append(f"  [{label}] @{handle}: ERROR {e!r}")
            continue
        findable += int(by_phrase)
        lines.append(
            f"  [{label}] @{handle}: post-search {'FINDABLE ✅' if by_phrase else 'not yet'}"
        )

    report = f"{stamp}\n" + "\n".join(lines) + "\n"
    print(report)
    with LOG.open("a") as fh:
        fh.write(report + "\n")
    _notify("FMML findability", f"{findable}/{len(accounts)} accounts findable")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
