# Paper reconciliation policy

The scheduled workflow uses alpaca_reconciled.py and the original paper execution engine. Existing account identity checks, durable order-intent checkpoints, client-ID deduplication and risk limits remain in place. Do not reset the state branch.

Confirmed fees come only from broker CFEE activities. Observed activities are retained by ID across temporarily incomplete responses. Reads are refreshed up to three times.

With allow_fee_pending_exits enabled, a negative quantity difference can be classified as fee_pending only when it matches the configured 25 bps cumulative buy-fee calculation, less recorded crypto fee quantities, within the existing 0.00000001 quantity tolerance. The unconfirmed amount is bounded by fills within 48 hours, rounded per fill to nine decimals. This is a narrowly scoped assumption, not proof that a fee posted. Other fee tiers or unexplained differences remain blocked.

Pending mode also requires filled bot buy orders linked to ledger cycles, no unfinished order for the mismatched symbol, a single active cycle for a positive holding, and a complete matching order-history snapshot since activation. Unknown orders, missing records, or 500-or-more history rows block this exception. No fee is fabricated or added to fees.csv.

All new buys are blocked during fee_pending, including after a cycle has exited, until confirmed fee records reconcile. Software exits may run only for the bot-owned active cycle and may sell no more than the refreshed broker quantity and qty_available. Exit evaluation still requires a fresh quote and remains subject to workflow/API availability; it is not a standing stop order.

Entry signal scans occur at most once per 1800 seconds; exit checks remain on the existing five-minute workflow cadence. The timer is durably checkpointed before scanning. Scans are skipped during pending fees or existing risk pauses. Eligible entries are not guaranteed trades.

Review reconciliation.csv, reconciliation.json and the journal. Fee-pending accounting is provisional even if the broker position is zero after an exit. Keep credentials private. This commit was checked with isolated simulated-broker tests, not a live Alpaca run or the full repository suite. GitHub runs the complete test suite before execution.
