"""Persona Dresser (ex-Profile Mutator) — applies/retires an identity.

Takes a warmed, OAuth-authorized account from the pipeline and applies the
generated identity (display name, bio, avatar) via the single developer app.
The @ handle is NEVER changed (X API cannot change handles). After the 1h reveal
window, retires the account: wipes it to a dormant state and schedules deletion.

The claim code is embedded in the bio — finding the persona is the only way to
read the code that the winner must DM to the main account.
"""

from __future__ import annotations

from ..social.x_client import MAX_BIO_LEN, Profile, XClient
from .generator import GeneratedPersona

# Neutral state a retired account is reset to (no game identity).
DORMANT_NAME = "—"
DORMANT_BIO = "just here for the vibes"


def compose_bio(base_bio: str, claim_code: str) -> str:
    """Put the claim code at the end of the bio, trimming to fit the 160 limit."""
    suffix = f"\ncode: {claim_code}"
    room = MAX_BIO_LEN - len(suffix)
    if room < 0:
        raise ValueError("claim code too long for a bio")
    return f"{base_bio[:room].rstrip()}{suffix}"


class PersonaDresser:
    def __init__(self, x_client: XClient):
        self._x = x_client

    def dress(
        self,
        *,
        access_token: str,
        access_secret: str,
        identity: GeneratedPersona,
        claim_code: str,
        avatar_path: str | None = None,
    ) -> Profile:
        """Apply identity + embed the claim code in the bio. Returns the profile
        X reports back, so the orchestrator can verify the write took."""
        bio = compose_bio(identity.bio, claim_code)
        if avatar_path:
            self._x.set_avatar(access_token, access_secret, avatar_path)
        return self._x.update_profile(
            access_token, access_secret, name=identity.display_name, description=bio
        )

    def retire(self, *, access_token: str, access_secret: str) -> Profile:
        """Reset the account to a neutral dormant state after the reveal window.
        The DB marks state 'retired' and sets delete_after (+30d) separately."""
        return self._x.update_profile(
            access_token, access_secret, name=DORMANT_NAME, description=DORMANT_BIO
        )
