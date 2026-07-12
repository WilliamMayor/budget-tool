"""Tests for sync/sync.py — sync orchestration."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from sync.db import get_all_accounts, get_transactions_for_account, insert_transaction
from sync.models import Transaction, TransactionStatus
from sync.sync import sync_account
from tests.conftest import make_transaction

# Anchor fixtures to recent dates so the strict backward walk reaches them.
TODAY = date.today()
RECENT = TODAY - timedelta(days=2)


def _make_client(transactions=None, balance=Decimal("0")):
    """Mock LunchflowClient whose get_transactions filters by the [from, to] window."""
    transactions = transactions or []
    client = MagicMock()

    def _get_transactions(account_id, date_from=None, date_to=None):
        return [
            tx for tx in transactions
            if (date_from is None or (tx.date and tx.date >= date_from))
            and (date_to is None or (tx.date and tx.date <= date_to))
        ]

    client.get_transactions.side_effect = _get_transactions
    client.get_balance.return_value = balance
    return client


def _make_api_tx(account_id, tx_date, amount=Decimal("10.00"), cdi="DBIT",
                 lunchflow_id="lf-1", status=TransactionStatus.BOOKED):
    return Transaction(
        account_id=account_id,
        lunchflow_id=lunchflow_id,
        amount=amount,
        currency="GBP",
        credit_debit_indicator=cdi,
        status=status,
        date=tx_date,
        merchant="Tesco",
    )


# ---------------------------------------------------------------------------
# Opening balance adjustor
# ---------------------------------------------------------------------------

def test_no_adjustor_when_balance_matches(db_conn, saved_account):
    # One DBIT of £10; net signed = -10; balance = -10 → no gap
    tx = _make_api_tx(saved_account.id, RECENT, amount=Decimal("10.00"), cdi="DBIT")
    client = _make_client([tx], balance=Decimal("-10.00"))

    sync_account(db_conn, client, saved_account)

    txns = get_transactions_for_account(db_conn, saved_account.id)
    opening = [t for t in txns if t.status == TransactionStatus.OPENING_BALANCE]
    assert len(opening) == 0


def test_adjustor_inserted_when_balance_does_not_match(db_conn, saved_account):
    # One DBIT of £10; net = -10; but balance = £90 → adjustor = 90 - (-10) = 100 CRDT
    tx = _make_api_tx(saved_account.id, RECENT, amount=Decimal("10.00"), cdi="DBIT")
    client = _make_client([tx], balance=Decimal("90.00"))

    sync_account(db_conn, client, saved_account)

    txns = get_transactions_for_account(db_conn, saved_account.id)
    opening = [t for t in txns if t.status == TransactionStatus.OPENING_BALANCE]
    assert len(opening) == 1
    assert opening[0].amount == Decimal("100.00")
    assert opening[0].credit_debit_indicator == "CRDT"


def test_adjustor_dated_one_day_before_earliest_transaction(db_conn, saved_account):
    tx = _make_api_tx(saved_account.id, RECENT, amount=Decimal("10.00"), cdi="DBIT")
    client = _make_client([tx], balance=Decimal("50.00"))

    sync_account(db_conn, client, saved_account)

    txns = get_transactions_for_account(db_conn, saved_account.id)
    opening = [t for t in txns if t.status == TransactionStatus.OPENING_BALANCE]
    assert opening[0].date == RECENT - timedelta(days=1)


def test_no_adjustor_when_no_transactions(db_conn, saved_account):
    client = _make_client([], balance=Decimal("0.00"))
    sync_account(db_conn, client, saved_account)
    txns = get_transactions_for_account(db_conn, saved_account.id)
    assert txns == []


def test_adjustor_not_duplicated_on_second_sync(db_conn, saved_account):
    tx = _make_api_tx(saved_account.id, RECENT, amount=Decimal("10.00"), cdi="DBIT")
    client = _make_client([tx], balance=Decimal("90.00"))

    sync_account(db_conn, client, saved_account)
    sync_account(db_conn, client, saved_account)  # second run

    txns = get_transactions_for_account(db_conn, saved_account.id)
    opening = [t for t in txns if t.status == TransactionStatus.OPENING_BALANCE]
    assert len(opening) == 1


# ---------------------------------------------------------------------------
# Upsert behaviour
# ---------------------------------------------------------------------------

def test_sync_inserts_new_transactions(db_conn, saved_account):
    txs = [
        _make_api_tx(saved_account.id, RECENT - timedelta(days=d), lunchflow_id=f"lf-{d}")
        for d in range(1, 4)
    ]
    client = _make_client(txs, balance=Decimal("-30.00"))

    result = sync_account(db_conn, client, saved_account)

    assert result["upserted"] == 3


def test_sync_updates_pending_to_booked(db_conn, saved_account):
    insert_transaction(
        db_conn,
        make_transaction(
            saved_account.id,
            lunchflow_id="lf-1",
            status=TransactionStatus.PENDING,
            date=RECENT,
        ),
    )
    tx = _make_api_tx(
        saved_account.id, RECENT,
        lunchflow_id="lf-1", status=TransactionStatus.BOOKED,
    )
    client = _make_client([tx], balance=Decimal("-10.00"))

    sync_account(db_conn, client, saved_account)

    txns = get_transactions_for_account(db_conn, saved_account.id)
    assert txns[0].status == TransactionStatus.BOOKED


def test_sync_preserves_note_on_update(db_conn, saved_account):
    insert_transaction(
        db_conn,
        make_transaction(saved_account.id, lunchflow_id="lf-1", note="keep me"),
    )
    tx = _make_api_tx(saved_account.id, RECENT, lunchflow_id="lf-1")
    client = _make_client([tx], balance=Decimal("-10.00"))

    sync_account(db_conn, client, saved_account)

    txns = get_transactions_for_account(db_conn, saved_account.id)
    assert txns[0].note == "keep me"


# ---------------------------------------------------------------------------
# Sync metadata
# ---------------------------------------------------------------------------

def test_sync_updates_last_synced_at(db_conn, saved_account):
    client = _make_client([], balance=Decimal("0.00"))
    sync_account(db_conn, client, saved_account)

    accounts = get_all_accounts(db_conn)
    account = next(a for a in accounts if a.id == saved_account.id)
    assert account.last_synced_at is not None


def test_sync_result_has_expected_keys(db_conn, saved_account):
    client = _make_client([], balance=Decimal("0.00"))
    result = sync_account(db_conn, client, saved_account)
    assert "lunchflow_id" in result
    assert "institution_name" in result
    assert "upserted" in result


def test_sync_creates_default_split_for_each_transaction(db_conn, saved_account):
    txs = [
        _make_api_tx(saved_account.id, RECENT - timedelta(days=d), lunchflow_id=f"lf-{d}")
        for d in range(1, 4)
    ]
    client = _make_client(txs, balance=Decimal("-30.00"))
    sync_account(db_conn, client, saved_account)

    for d in range(1, 4):
        tx_row = db_conn.execute(
            "SELECT id FROM transactions WHERE lunchflow_id = ?", (f"lf-{d}",)
        ).fetchone()
        split = db_conn.execute(
            "SELECT * FROM splits WHERE transaction_id = ? AND is_default = 1",
            (tx_row["id"],),
        ).fetchone()
        assert split is not None, f"No default split for lf-{d}"


def test_sync_creates_round_up_split_when_enabled(db_conn, saved_account):
    db_conn.execute(
        "UPDATE accounts SET round_up_since = '2025-01-01' WHERE id = ?",
        (saved_account.id,),
    )
    db_conn.commit()

    tx = _make_api_tx(
        saved_account.id, RECENT,
        amount=Decimal("4.75"), cdi="DBIT", lunchflow_id="lf-roundup"
    )
    client = _make_client([tx], balance=Decimal("-4.75"))
    sync_account(db_conn, client, saved_account)

    tx_row = db_conn.execute(
        "SELECT id FROM transactions WHERE lunchflow_id = 'lf-roundup'"
    ).fetchone()
    split = db_conn.execute(
        "SELECT amount FROM splits WHERE transaction_id = ? AND is_round_up = 1",
        (tx_row["id"],),
    ).fetchone()
    assert split is not None
    assert split["amount"] == "0.25"


def test_sync_no_round_up_split_before_enabled_date(db_conn, saved_account):
    tx = _make_api_tx(
        saved_account.id, RECENT,
        amount=Decimal("4.75"), cdi="DBIT", lunchflow_id="lf-before"
    )
    db_conn.execute(
        "UPDATE accounts SET round_up_since = ? WHERE id = ?",
        ((RECENT + timedelta(days=1)).isoformat(), saved_account.id),
    )
    db_conn.commit()

    client = _make_client([tx], balance=Decimal("-4.75"))
    sync_account(db_conn, client, saved_account)

    tx_row = db_conn.execute(
        "SELECT id FROM transactions WHERE lunchflow_id = 'lf-before'"
    ).fetchone()
    split = db_conn.execute(
        "SELECT * FROM splits WHERE transaction_id = ? AND is_round_up = 1",
        (tx_row["id"],),
    ).fetchone()
    assert split is None


# ---------------------------------------------------------------------------
# First-sync vs incremental-sync path selection
# ---------------------------------------------------------------------------

def test_first_sync_uses_backward_walk_and_sets_opening_balance(db_conn, saved_account):
    # No stored transactions -> first sync. Balance mismatch -> adjustor.
    tx = _make_api_tx(saved_account.id, RECENT, amount=Decimal("10.00"), cdi="DBIT")
    client = _make_client([tx], balance=Decimal("90.00"))

    sync_account(db_conn, client, saved_account)

    txns = get_transactions_for_account(db_conn, saved_account.id)
    opening = [t for t in txns if t.status == TransactionStatus.OPENING_BALANCE]
    assert len(opening) == 1
    # Balance was fetched on the first-sync path.
    client.get_balance.assert_called_once()


def test_incremental_sync_does_not_add_opening_balance(db_conn, saved_account):
    # Pre-existing transaction -> since is set -> incremental path.
    insert_transaction(
        db_conn, make_transaction(saved_account.id, lunchflow_id="old", date=RECENT)
    )
    new_tx = _make_api_tx(
        saved_account.id, RECENT, lunchflow_id="new", amount=Decimal("10.00"), cdi="DBIT"
    )
    # Deliberately mismatched balance: incremental path must NOT insert an adjustor.
    client = _make_client([new_tx], balance=Decimal("5000.00"))

    sync_account(db_conn, client, saved_account)

    txns = get_transactions_for_account(db_conn, saved_account.id)
    opening = [t for t in txns if t.status == TransactionStatus.OPENING_BALANCE]
    assert opening == []
    client.get_balance.assert_not_called()


def test_incremental_sync_fetches_from_last_synced_day_inclusive(db_conn, saved_account):
    insert_transaction(
        db_conn, make_transaction(saved_account.id, lunchflow_id="old", date=RECENT)
    )
    client = _make_client([], balance=Decimal("0.00"))

    sync_account(db_conn, client, saved_account)

    first_call = client.get_transactions.call_args_list[0]
    assert first_call.kwargs["date_from"] == RECENT
