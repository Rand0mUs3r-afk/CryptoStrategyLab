# Alpaca crypto PAPER bot

Status: FAILED_CLOSED
Dedicated paper account only. Broker fills, not virtual experiment fills.
TP/SL are software checks at workflow runs, NOT standing bracket orders.
Coinbase closed candles produce signals; fresh Alpaca quotes price decisions.
Fees can post later. P&L below is before USD fees; no fabricated net performance.

Reason: Position/fee reconciliation mismatch for ETHUSD; wait for fees or review manual activity

## Entry diagnostics

Candidates: 0. Skipped: 0. Broker order results: 0.
Broker order results are not proof of fills; see orders.csv.

No candidates recorded; check run status and data errors before concluding there were no signals.


Per-candidate decisions: entry_decisions.csv. Quotes checked for entries: quotes.csv.

## Open / pending positions

| Coin | Bar | Strategy | Entry | Filled qty | Entry dollars | Remaining | TP | SL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ETH/USD | 15m | trend_pullback | n/a | n/a | n/a | 0.0 | n/a | n/a | pending |
## Closed cycles

| Coin | Bar | Strategy | Entry | Filled qty | Entry dollars | Remaining | TP | SL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Order IDs, fill prices/times and quantities: orders.csv.
Closed trade cashflows: closed_trades.csv. Broker-reported fees: fees.csv.
Dust is kept in the ledger; it is not silently written off or counted as a win.
