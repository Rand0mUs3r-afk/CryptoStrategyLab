# Alpaca crypto PAPER bot

Status: FAILED_CLOSED
Dedicated paper account only. Broker fills, not virtual experiment fills.
TP/SL are software checks at workflow runs, NOT standing bracket orders.
Coinbase closed candles produce signals; fresh Alpaca quotes price decisions.
Fees can post later. P&L below is before USD fees; no fabricated net performance.

Reason: Position/fee reconciliation mismatch for SOLUSD: expected=1.962246379, broker=1.957340763, difference=-0.004905616, recorded_fee_quantity=0; unresolved after 3 read-only attempts. No fee inferred or position adopted; entries and automated exits blocked. Review reconciliation.csv and the paper holding.

## Entry diagnostics

Candidates: 0. Skipped: 0. Broker order results: 0.
Broker order results are not proof of fills; see orders.csv.

No candidates recorded; check run status and data errors before concluding there were no signals.


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

## Reconciliation

Status: mismatch
Read-only attempts: 3

| Coin | Expected | Broker | Difference |
| --- | --- | --- | --- |
| ETHUSD | 0.08480340 | 0.0848034 | 0E-8 |
| SOLUSD | 1.962246379 | 1.957340763 | -0.004905616 |

UNRESOLVED: new entries and automated exits are blocked. Review the paper holding. No missing fee has been invented.

Full diagnostics: reconciliation.csv and reconciliation.json.
