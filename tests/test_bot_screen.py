from finding_memeland.dm.validator import DMValidator, ParsedDM, screen_bot


def test_blocks_bot_in_handle():
    ok, reason = screen_bot(display_name="Cool Trader", handle="@trade_bot",
                            bio="gm", automated_label=False)
    assert not ok and "handle" in reason


def test_blocks_agent_in_name():
    ok, _ = screen_bot(display_name="Solver Agent", handle="@solver",
                       bio="gm", automated_label=False)
    assert not ok


def test_blocks_automated_label():
    ok, reason = screen_bot(display_name="Anon", handle="@anon", bio="gm",
                            automated_label=True)
    assert not ok and "Automated" in reason


def test_blocks_our_own_account():
    ok, reason = screen_bot(display_name="x", handle="@FindingMemeland", bio="",
                            automated_label=False, own_handles=["@findingmemeland"])
    assert not ok and "own account" in reason


def test_allows_human_who_merely_mentions_ai_in_bio():
    # "I love AI" must NOT disqualify a human.
    ok, _ = screen_bot(display_name="Jane", handle="@jane_eth",
                       bio="I love AI and coffee", automated_label=False)
    assert ok


def test_blocks_explicit_bot_phrase_in_bio():
    ok, _ = screen_bot(display_name="Jane", handle="@jane_eth",
                       bio="automated account, beep boop", automated_label=False)
    assert not ok


def test_allows_normal_human():
    ok, reason = screen_bot(display_name="Pedro M", handle="@montepep",
                           bio="building things on Base", automated_label=False)
    assert ok and reason is None


# --- validator integration: bot check is the LAST filter ---
class _ChainOK:
    def has_continuous_holding(self, **kw):
        return True


class _XOK:
    def has_reshared(self, **kw):
        return True


def _hunt():
    class H:
        claim_code = "ABCDEFGH"
        min_balance_fmml = 1
        holding_hours = 48
        reshare_post_id = "t1"
    return H()


def test_validator_disqualifies_disclosed_bot_even_if_eligible():
    v = DMValidator(
        chain=_ChainOK(), x_client=_XOK(),
        profile_lookup=lambda uid: {"name": "Sniper Bot", "handle": "@x", "bio": ""},
    )
    dm = ParsedDM(dm_id="d", sender_x_id="9", wallet="0x" + "a" * 40, claim_code="ABCDEFGH")
    res = v.validate(dm, _hunt())
    assert not res.won and res.outcome == "bot_disqualified"


def test_validator_passes_clean_human():
    v = DMValidator(
        chain=_ChainOK(), x_client=_XOK(),
        profile_lookup=lambda uid: {"name": "Jane", "handle": "@jane", "bio": "gm"},
    )
    dm = ParsedDM(dm_id="d", sender_x_id="9", wallet="0x" + "a" * 40, claim_code="ABCDEFGH")
    res = v.validate(dm, _hunt())
    assert res.won and res.outcome == "won"
