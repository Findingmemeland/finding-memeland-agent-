"""X (Twitter) API wrapper — single developer app, many authorized accounts.

One app (on the main account) holds OAuth tokens for the main account AND every
persona. Reads are billed per result returned; design every call to minimize
billed reads (empty inbox = free; never put URLs in posts).

Profile read/write uses OAuth 1.0a user context (v1.1 endpoints) — these are the
methods we need first (Persona Dresser), and the ones whose availability in the
current pay-per-use tier we must validate empirically.

Posting, DM read/reply and reshare lookups (v2) are stubbed for later steps.
"""

from __future__ import annotations

from dataclasses import dataclass

import tweepy

# X profile field limits.
MAX_NAME_LEN = 50
MAX_BIO_LEN = 160


@dataclass(frozen=True)
class Profile:
    user_id: str
    screen_name: str
    name: str
    description: str


class XClient:
    def __init__(self, *, api_key: str, api_secret: str, bearer_token: str = ""):
        self._api_key = api_key
        self._api_secret = api_secret
        self._bearer = bearer_token

    # ------------------------------------------------------------------
    # OAuth 1.0a user context (v1.1) — profile read/write
    # ------------------------------------------------------------------
    def _api_for(self, access_token: str, access_secret: str) -> tweepy.API:
        auth = tweepy.OAuth1UserHandler(
            self._api_key, self._api_secret, access_token, access_secret
        )
        return tweepy.API(auth)

    def get_profile(self, access_token: str, access_secret: str) -> Profile:
        """Read the authenticated account's current profile (v1.1)."""
        me = self._api_for(access_token, access_secret).verify_credentials(
            skip_status=True, include_entities=False
        )
        return Profile(
            user_id=me.id_str,
            screen_name=me.screen_name,
            name=me.name or "",
            description=getattr(me, "description", "") or "",
        )

    def update_profile(
        self,
        access_token: str,
        access_secret: str,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Profile:
        """Update display name and/or bio (v1.1 account/update_profile).

        Returns the profile as reported back by X after the write, so callers
        can verify the change actually took.
        """
        if name is not None and len(name) > MAX_NAME_LEN:
            raise ValueError(f"name exceeds {MAX_NAME_LEN} chars")
        if description is not None and len(description) > MAX_BIO_LEN:
            raise ValueError(f"bio exceeds {MAX_BIO_LEN} chars")

        kwargs: dict[str, str] = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if not kwargs:
            raise ValueError("nothing to update")

        updated = self._api_for(access_token, access_secret).update_profile(**kwargs)
        return Profile(
            user_id=updated.id_str,
            screen_name=updated.screen_name,
            name=updated.name or "",
            description=getattr(updated, "description", "") or "",
        )

    def set_avatar(self, access_token: str, access_secret: str, image_path: str) -> None:
        """Set the profile image from a local file (v1.1 update_profile_image)."""
        self._api_for(access_token, access_secret).update_profile_image(image_path)

    # ------------------------------------------------------------------
    # v2 endpoints — implemented in later steps
    # ------------------------------------------------------------------
    def post(self, text: str, *, as_account: str = "main", long_post: bool = False) -> str:
        raise NotImplementedError("post — implemented in step 24/26")

    def read_dms(self, *, since_id: str | None) -> list[dict]:
        raise NotImplementedError("read_dms — implemented in step 26")

    def send_dm_reply(self, *, recipient_x_id: str, text: str) -> None:
        raise NotImplementedError("send_dm_reply — implemented in step 26")

    def has_reshared(self, *, user_id: str, post_id: str) -> bool:
        raise NotImplementedError("has_reshared — implemented in step 26")
