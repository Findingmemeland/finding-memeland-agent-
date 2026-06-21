from datetime import datetime, timedelta, timezone

from finding_memeland.chain.holdings import Holdings

NOW = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)


class _Repo:
    def __init__(self, samples):
        self._samples = samples
        self.added = []

    def holding_samples(self, wallet, since):
        return [s for s in self._samples if s["sampled_at"] >= since]

    def add_holding_sample(self, wallet, balance):
        self.added.append((wallet, balance))


class _Holdings(Holdings):
    """current_balance overridden so we don't need web3."""

    def __init__(self, repo, current):
        super().__init__(web3=None, token_address="0xt", repo=repo, now_fn=lambda: NOW)
        self._current = current

    def current_balance(self, wallet):
        return self._current


def _sample(hours_ago, balance):
    return {"balance_fmml": balance, "sampled_at": NOW - timedelta(hours=hours_ago)}


def test_continuous_holding_passes():
    repo = _Repo([_sample(47, 100), _sample(23, 100), _sample(1, 100)])
    h = _Holdings(repo, current=100)
    assert h.has_continuous_holding(wallet="0xw", min_balance=50, holding_hours=48)


def test_current_below_floor_fails():
    repo = _Repo([_sample(47, 100), _sample(1, 100)])
    h = _Holdings(repo, current=10)
    assert not h.has_continuous_holding(wallet="0xw", min_balance=50, holding_hours=48)


def test_a_dip_below_floor_fails():
    repo = _Repo([_sample(47, 100), _sample(23, 5), _sample(1, 100)])
    h = _Holdings(repo, current=100)
    assert not h.has_continuous_holding(wallet="0xw", min_balance=50, holding_hours=48)


def test_no_history_fails():
    h = _Holdings(_Repo([]), current=100)
    assert not h.has_continuous_holding(wallet="0xw", min_balance=50, holding_hours=48)


def test_insufficient_early_coverage_fails():
    # Bought recently: only a sample 1h ago, nothing back near the window start.
    repo = _Repo([_sample(1, 100)])
    h = _Holdings(repo, current=100)
    assert not h.has_continuous_holding(wallet="0xw", min_balance=50, holding_hours=48)


def test_sample_balance_persists():
    repo = _Repo([])
    h = _Holdings(repo, current=777)
    assert h.sample_balance("0xw") == 777
    assert repo.added == [("0xw", 777)]
