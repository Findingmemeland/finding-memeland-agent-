"""DBPersonaSource — the Orchestrator's PersonaSource port, backed by Supabase.

Hands the orchestrator the next warmed, OAuth-authorized account from the
pipeline and marks accounts in_play / retired. OAuth tokens are NOT stored in the
DB; they're resolved at use time from Doppler/env by the persona's oauth_ref.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..orchestrator.ports import ReadyPersona

DELETE_AFTER_DAYS = 30


class DBPersonaSource:
    def __init__(self, repo, token_resolver):
        self._repo = repo
        self._resolve = token_resolver  # callable(oauth_ref) -> (token, secret)

    def acquire_ready(self) -> ReadyPersona:
        row = self._repo.next_ready_persona()
        if not row:
            raise RuntimeError("no 'ready' persona in the pipeline — warm/authorize more")
        token, secret = self._resolve(row["oauth_ref"])
        self._repo.set_persona_state(row["id"], "in_play")
        return ReadyPersona(
            id=row["id"],
            handle=row["handle"],
            x_user_id=row["x_user_id"],
            access_token=token,
            access_secret=secret,
        )

    def mark_retired(self, persona_id: str) -> None:
        delete_after = (datetime.now(timezone.utc) + timedelta(days=DELETE_AFTER_DAYS)).isoformat()
        self._repo.set_persona_state(persona_id, "retired", delete_after=delete_after)
