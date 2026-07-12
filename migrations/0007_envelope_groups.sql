-- Envelope groups: a per-account tree of named, tintable folders that can
-- nest inside each other and hold envelopes. Additive and backwards
-- compatible — existing envelopes stay ungrouped (group_id NULL = top level).

CREATE TABLE IF NOT EXISTS envelope_groups (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id  INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    parent_id   INTEGER REFERENCES envelope_groups(id) ON DELETE CASCADE,
    name        TEXT    NOT NULL,
    tint        TEXT    NOT NULL DEFAULT 'budget',
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Envelopes gain an optional group. ON DELETE SET NULL: removing a group
-- never deletes its envelopes — they fall back to the account's top level.
ALTER TABLE envelopes ADD COLUMN group_id INTEGER REFERENCES envelope_groups(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_envelope_groups_account ON envelope_groups(account_id);
CREATE INDEX IF NOT EXISTS idx_envelope_groups_parent  ON envelope_groups(parent_id);
CREATE INDEX IF NOT EXISTS idx_envelopes_group_id      ON envelopes(group_id);
