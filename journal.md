# Alpaca crypto PAPER bot

Status: FAILED_CLOSED
Dedicated paper account only. Broker fills, not virtual experiment fills.
TP/SL are software checks at workflow runs, NOT standing bracket orders.
Coinbase closed candles produce signals; fresh Alpaca quotes price decisions.
Fees can post later. P&L below is before USD fees; no fabricated net performance.

Reason: Position/fee reconciliation mismatch for SOLUSD; wait for fees or review manual activity

## Entry diagnostics

Candidates: 3. Skipped: 0. Broker order results: 1.
Broker order results are not proof of fills; see orders.csv.

| Coin | Bar | Strategy | Outcome | Reason | Details |
| --- | --- | --- | --- | --- | --- |
| SOL/USD | 5m | trend_pullback | order_result | broker_order_returned | {"broker_order_id": "dc7c9a52-6fd5-41c7-9ad9-cad5afcf142e", "broker_status": "pending_new", "client_order_id": "csl2-84210358f84e330b449fc563d39e4a32", "quantity": "1.962246379", "reference_ask": 101.924} |

Per-candidate decisions: entry_decisions.csv. Quotes checked for entries: quotes.csv.

## Open / pending positions

| Coin | Bar | Strategy | Entry | Filled qty | Entry dollars | Remaining | TP | SL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ETH/USD | 15m | trend_pullback | 2352.83 | 0.08501594 | 200.0280541102 | 0.0848034 | 2368.832612413611 | 2344.8286937931944 | open |
| SOL/USD | 5m | trend_pullback | n/a | n/a | n/a | 0.0 | n/a | n/a | pending |
## Closed cycles

| Coin | Bar | Strategy | Entry | Filled qty | Entry dollars | Remaining | TP | SL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Order IDs, fill prices/times and quantities: orders.csv.
Closed trade cashflows: closed_trades.csv. Broker-reported fees: fees.csv.
Dust is kept in the ledger; it is not silently written off or counted as a win.
