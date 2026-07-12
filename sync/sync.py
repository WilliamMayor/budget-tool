"""
Sync orchestration: fetches transactions and balance from Lunchflow,
upserts transactions by lunchflow_id, and inserts an opening balance
adjustor if the fetched history doesn't account for the full balance.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import httpx

from .db import (
    get_all_accounts,
    get_latest_transaction_date,
    has_opening_balance,
    insert_transaction,
    update_account_sync_info,
    upsert_transaction,
    ensure_default_split,
    ensure_round_up_split,
)
from .models import Account, Transaction, TransactionStatus


_MAX_BLANK_MONTHS = 6


def _last_day_of_month(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def _prev_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _fetch_full_history(client: object, lunchflow_id: int, today: date) -> list[Transaction]:
    """First-sync walk: step back month-by-month from `today`, stopping after
    _MAX_BLANK_MONTHS consecutive empty months. Returns every transaction found."""
    collected: list[Transaction] = []
    consecutive_blank = 0
    year, month = today.year, today.month
    while consecutive_blank < _MAX_BLANK_MONTHS:
        window_start = date(year, month, 1)
        window_end = min(_last_day_of_month(year, month), today)
        window = client.get_transactions(  # type: ignore[attr-defined]
            lunchflow_id, date_from=window_start, date_to=window_end
        )
        if window:
            collected.extend(window)
            consecutive_blank = 0
        else:
            consecutive_blank += 1
        year, month = _prev_month(year, month)
    return collected


def _fetch_incremental(
    client: object, lunchflow_id: int, since: date, today: date
) -> list[Transaction]:
    """Incremental walk: one inclusive [from, to] calendar-month window from
    `since` to `today` (each capped at `today`). Returns every transaction found."""
    collected: list[Transaction] = []
    window_start = since
    while window_start <= today:
        window_end = min(_last_day_of_month(window_start.year, window_start.month), today)
        collected.extend(
            client.get_transactions(  # type: ignore[attr-defined]
                lunchflow_id, date_from=window_start, date_to=window_end
            )
        )
        window_start = window_end + timedelta(days=1)
    return collected


def _maybe_insert_opening_balance(
    conn: sqlite3.Connection,
    account: Account,
    api_transactions: list[Transaction],
    current_balance: Decimal,
) -> None:
    """First-sync only: if the fetched history's signed sum doesn't match the
    balance and no opening balance exists yet, insert a correcting adjustor
    dated one day before the earliest fetched transaction."""
    if not api_transactions:
        return

    expected_balance = sum(
        (tx.amount if tx.credit_debit_indicator == "CRDT" else -tx.amount)
        for tx in api_transactions
    )
    if expected_balance == current_balance or has_opening_balance(conn, account.id):  # type: ignore[arg-type]
        return

    earliest_date = min((tx.date for tx in api_transactions if tx.date), default=None)
    if earliest_date is None:
        return

    adjustor_signed = current_balance - expected_balance
    if adjustor_signed < 0:
        cdi = "DBIT"
        adj_amount = -adjustor_signed
    else:
        cdi = "CRDT"
        adj_amount = adjustor_signed

    saved_adjustor = insert_transaction(
        conn,
        Transaction(
            account_id=account.id,  # type: ignore[arg-type]
            amount=adj_amount,
            currency=account.currency,
            credit_debit_indicator=cdi,
            status=TransactionStatus.OPENING_BALANCE,
            date=earliest_date - timedelta(days=1),
            merchant="Balance correction",
            description="Your transaction history only goes back so far. This entry makes the opening balance match your actual account balance — allocate it to cover any spending that happened before your history begins.",
        ),
    )
    assert saved_adjustor.id is not None
    ensure_default_split(conn, saved_adjustor.id)


def sync_account(conn: sqlite3.Connection, client: object, account: Account) -> dict:
    """
    Sync transactions for a single account. Returns a summary dict.
    Raises httpx.HTTPError on API errors — the caller is responsible for handling these.
    """
    today = datetime.now(timezone.utc).date()
    since = get_latest_transaction_date(conn, account.id)  # type: ignore[arg-type]

    if since is None:
        # First sync: discover the full available history, then reconcile the balance.
        api_transactions = _fetch_full_history(client, account.lunchflow_id, today)
        current_balance: Decimal = client.get_balance(account.lunchflow_id)  # type: ignore[attr-defined]
        _maybe_insert_opening_balance(conn, account, api_transactions, current_balance)
    else:
        # Incremental: re-fetch from the start of the month before the last
        # synced day, so backdated posts and late pending->booked transitions
        # in recent history are still picked up (upsert dedupes the overlap).
        prev_year, prev_month = _prev_month(since.year, since.month)
        look_back_start = date(prev_year, prev_month, 1)
        api_transactions = _fetch_incremental(client, account.lunchflow_id, look_back_start, today)

    for tx in api_transactions:
        tx.account_id = account.id  # type: ignore[assignment]
        saved = upsert_transaction(conn, tx)
        assert saved.id is not None
        ensure_default_split(conn, saved.id)  # type: ignore[arg-type]
        ensure_round_up_split(conn, saved.id)  # type: ignore[arg-type]

    now = datetime.now(timezone.utc)
    update_account_sync_info(conn, account.id, now)  # type: ignore[arg-type]

    return {
        "lunchflow_id": account.lunchflow_id,
        "institution_name": account.institution_name,
        "upserted": len(api_transactions),
    }


def sync_all(conn: sqlite3.Connection, client: object) -> list[dict]:
    """Sync every registered account. Returns a list of per-account result dicts."""
    accounts = get_all_accounts(conn)
    if not accounts:
        print("No accounts found. Connect banks in the Lunchflow dashboard.")
        return []

    results = []
    for account in accounts:
        label = f"{account.institution_name or 'Unknown'} / {account.name or account.lunchflow_id}"
        print(f"Syncing {label}...")
        try:
            result = sync_account(conn, client, account)
            results.append(result)
            print(f"  {result['upserted']} transaction(s) synced")
        except httpx.HTTPError as e:
            print(f"  Failed: {e}")
            results.append({
                "lunchflow_id": account.lunchflow_id,
                "institution_name": account.institution_name,
                "error": str(e),
            })

    return results
