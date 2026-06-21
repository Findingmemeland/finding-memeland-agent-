from datetime import datetime, timezone

from finding_memeland.db.client import Repo


class _Query:
    def __init__(self, table, log):
        self._t = table
        self._log = log
        self._op = None
        self._payload = None
        self._filters = []

    def insert(self, payload):
        self._op, self._payload = "insert", payload
        return self

    def update(self, payload):
        self._op, self._payload = "update", payload
        return self

    def select(self, cols):
        self._op = "select"
        return self

    def eq(self, c, v):
        self._filters.append(("eq", c, v))
        return self

    def gte(self, c, v):
        self._filters.append(("gte", c, v))
        return self

    def order(self, c):
        return self

    def limit(self, n):
        return self

    def execute(self):
        self._log.append({"table": self._t, "op": self._op, "payload": self._payload,
                          "filters": self._filters})
        if self._t == "hunts" and self._op == "insert":
            return _Resp([{"id": 42}])
        if self._op == "select":
            return _Resp([])
        return _Resp([{}])


class _Resp:
    def __init__(self, data):
        self.data = data


class _FakeDB:
    def __init__(self):
        self.log = []

    def table(self, name):
        return _Query(name, self.log)


def test_create_hunt_returns_id():
    db = _FakeDB()
    assert Repo(db).create_hunt(claim_code="ABCDEFGH", holding_hours=48) == 42


def test_log_submission_serializes_datetime():
    db = _FakeDB()
    when = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    Repo(db).log_submission(hunt_id=1, dm_id="d", x_created_at=when, outcome="won")
    entry = db.log[-1]
    assert entry["table"] == "submissions" and entry["op"] == "insert"
    assert entry["payload"]["x_created_at"] == when.isoformat()


def test_set_hunt_state_updates_with_filter():
    db = _FakeDB()
    Repo(db).set_hunt_state(7, "live")
    entry = db.log[-1]
    assert entry["op"] == "update" and entry["payload"]["state"] == "live"
    assert ("eq", "id", 7) in entry["filters"]


def test_holding_samples_filters_by_wallet_and_since():
    db = _FakeDB()
    since = datetime(2026, 8, 1, tzinfo=timezone.utc)
    Repo(db).holding_samples("0xabc", since)
    entry = db.log[-1]
    assert entry["table"] == "holding_samples"
    assert ("eq", "wallet", "0xabc") in entry["filters"]
    assert ("gte", "sampled_at", since.isoformat()) in entry["filters"]
