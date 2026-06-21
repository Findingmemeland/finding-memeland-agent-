"""On-chain holding checks against Base.

Continuity matters (anti-sniper): a wallet must have held >= the floor across the
whole window, not just at submission. A daily job samples balances into
holding_samples; at validation we require every sample in the window to meet the
floor, with coverage back to the window start, plus a live balance check now.
Smart-contract wallets (Safes) are allowed, not just EOAs.

Balances are handled in WHOLE tokens (consistent with the prize/cap and the
hunt's min_balance_fmml). The web3 client is injected — no top-level web3 import.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

# Minimal ERC-20 ABI — balanceOf only.
ERC20_BALANCEOF_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    }
]

# Daily sampling cadence + slack: how far after window-start the earliest sample
# may be and still count as "covering" the window.
MAX_COVERAGE_GAP = timedelta(hours=26)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Holdings:
    def __init__(self, *, web3, token_address: str, repo, decimals: int = 18, now_fn=_utcnow):
        self._w3 = web3
        self._token_address = token_address
        self._repo = repo
        self._decimals = decimals
        self._now = now_fn

    def current_balance(self, wallet: str) -> int:
        """Live balance in WHOLE tokens (floored)."""
        contract = self._w3.eth.contract(
            address=self._w3.to_checksum_address(self._token_address),
            abi=ERC20_BALANCEOF_ABI,
        )
        base = contract.functions.balanceOf(
            self._w3.to_checksum_address(wallet)
        ).call()
        return base // (10 ** self._decimals)

    def sample_balance(self, wallet: str) -> int:
        """Read current balance and persist a holding_samples row (daily job)."""
        bal = self.current_balance(wallet)
        self._repo.add_holding_sample(wallet, bal)
        return bal

    def has_continuous_holding(self, *, wallet: str, min_balance: int, holding_hours: int) -> bool:
        """True iff the floor was held continuously across the window.

        Requires: live balance >= floor; at least one historical sample; every
        sample in the window >= floor; and coverage back to the window start
        (earliest sample no later than window_start + MAX_COVERAGE_GAP). Missing
        early history => False (cannot prove continuity — anti-sniper).
        """
        now = self._now()
        window_start = now - timedelta(hours=holding_hours)

        if self.current_balance(wallet) < min_balance:
            return False

        samples = self._repo.holding_samples(wallet, window_start)
        if not samples:
            return False

        balances = [int(s["balance_fmml"]) for s in samples]
        if any(b < min_balance for b in balances):
            return False

        earliest = min(_as_dt(s["sampled_at"]) for s in samples)
        if earliest > window_start + MAX_COVERAGE_GAP:
            return False

        return True


def _as_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))
