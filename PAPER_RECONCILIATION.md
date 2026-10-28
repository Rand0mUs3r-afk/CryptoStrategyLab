# Paper reconciliation and entry policy

The workflow uses alpaca_watchlist.py, alpaca_reconciled.py and the existing paper engine. Account identity checks, durable checkpoints, client-ID deduplication, ownership validation and position/risk limits remain in force. Do not reset the state branch.

At the user's request, estimated_fee_bps is zero for sizing. This is a modeling assumption, not a claim that Alpaca charges no crypto fees. Broker-reported cash, holdings and confirmed CFEE activities are never overwritten or zeroed.

allow_fee_pending_entries is explicitly enabled. After existing pending-fee checks validate a fee-sized discrepancy and matching order history, the journal retains fee_pending and provisional accounting but sets entries_blocked false. New setups can be scanned and eligible buys submitted without waiting solely for that fee activity to post. Setting this option false restores the former pause.

Unexplained discrepancies still block trading. The pending exception retains its configured 25 bps validation calculation, 48-hour recent-fill bound, quantity tolerance and ownership checks. The 25 bps value is not charged or reserved by the sizing model. Unknown orders, missing history or truncated history are not adopted.

Software exits use no more than the refreshed broker quantity and qty_available. Entry scans remain at most once per 1800 seconds and exit checks retain the existing five-minute workflow cadence. No forced purchases, ledger resets or live-account routes are added.

Regression tests are included for the new entry exception. This change has not been run locally against the full repository suite or live Alpaca; the workflow runs repository tests before trading.
