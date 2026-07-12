"""Unit tests for the month-window walk helpers in sync/sync.py."""

from datetime import date, timedelta

from sync.sync import _fetch_full_history, _fetch_incremental, _last_day_of_month, _prev_month
from tests.conftest import make_transaction


class _WindowClient:
    """Fake client returning only transactions whose date falls in [from, to].
    Records every (date_from, date_to) it is called with."""

    def __init__(self, transactions):
        self._transactions = transactions
        self.calls = []

    def get_transactions(self, account_id, date_from=None, date_to=None):
        self.calls.append((date_from, date_to))
        return [
            tx for tx in self._transactions
            if (date_from is None or (tx.date and tx.date >= date_from))
            and (date_to is None or (tx.date and tx.date <= date_to))
        ]


def test_last_day_of_month():
    assert _last_day_of_month(2025, 2) == date(2025, 2, 28)
    assert _last_day_of_month(2024, 2) == date(2024, 2, 29)
    assert _last_day_of_month(2025, 12) == date(2025, 12, 31)
    assert _last_day_of_month(2025, 4) == date(2025, 4, 30)


def test_prev_month():
    assert _prev_month(2025, 7) == (2025, 6)
    assert _prev_month(2025, 1) == (2024, 12)


def test_backward_walk_stops_after_six_blank_months():
    client = _WindowClient([])
    today = date(2026, 7, 12)
    result = _fetch_full_history(client, 1, today)
    assert result == []
    assert len(client.calls) == 6


def test_backward_walk_collects_recent_history():
    today = date(2026, 7, 12)
    tx = make_transaction(1, lunchflow_id="a", date=date(2026, 7, 5))
    client = _WindowClient([tx])
    result = _fetch_full_history(client, 1, today)
    assert result == [tx]
    # current month has data (reset), then 6 blank months -> 7 windows.
    assert len(client.calls) == 7


def test_backward_walk_finds_history_two_months_back_then_stops():
    today = date(2026, 7, 12)
    tx = make_transaction(1, lunchflow_id="a", date=date(2026, 5, 20))
    client = _WindowClient([tx])
    result = _fetch_full_history(client, 1, today)
    assert result == [tx]


def test_backward_walk_ignores_history_beyond_six_blank_months():
    # Strict rule: latest activity is 7 months before today -> never reached.
    today = date(2026, 7, 12)
    tx = make_transaction(1, lunchflow_id="a", date=date(2025, 12, 5))
    client = _WindowClient([tx])
    result = _fetch_full_history(client, 1, today)
    assert result == []


def test_backward_walk_current_window_capped_at_today():
    today = date(2026, 7, 12)
    client = _WindowClient([])
    _fetch_full_history(client, 1, today)
    # First window is the current month, from the 1st to today (not month end).
    assert client.calls[0] == (date(2026, 7, 1), date(2026, 7, 12))


def test_forward_walk_single_window_for_within_month_since():
    today = date(2026, 7, 12)
    tx = make_transaction(1, lunchflow_id="a", date=date(2026, 7, 8))
    client = _WindowClient([tx])
    result = _fetch_incremental(client, 1, date(2026, 7, 1), today)
    assert result == [tx]
    assert client.calls == [(date(2026, 7, 1), date(2026, 7, 12))]


def test_forward_walk_windows_are_contiguous_and_capped_at_today():
    today = date(2026, 7, 12)
    client = _WindowClient([])
    _fetch_incremental(client, 1, date(2026, 5, 10), today)
    # since is mid-May -> May(10-31), June(1-30), July(1-12)
    assert client.calls == [
        (date(2026, 5, 10), date(2026, 5, 31)),
        (date(2026, 6, 1), date(2026, 6, 30)),
        (date(2026, 7, 1), date(2026, 7, 12)),
    ]


def test_forward_walk_collects_across_windows():
    today = date(2026, 7, 12)
    txs = [
        make_transaction(1, lunchflow_id="may", date=date(2026, 5, 20)),
        make_transaction(1, lunchflow_id="jun", date=date(2026, 6, 15)),
        make_transaction(1, lunchflow_id="jul", date=date(2026, 7, 3)),
    ]
    client = _WindowClient(txs)
    result = _fetch_incremental(client, 1, date(2026, 5, 1), today)
    assert {tx.lunchflow_id for tx in result} == {"may", "jun", "jul"}


def test_forward_walk_no_windows_when_since_after_today():
    today = date(2026, 7, 12)
    client = _WindowClient([])
    result = _fetch_incremental(client, 1, date(2026, 7, 20), today)
    assert result == []
    assert client.calls == []
