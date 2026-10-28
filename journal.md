# Alpaca crypto PAPER bot

Status: PAPER_TICK_COMPLETED
Dedicated paper account only. Broker fills, not virtual experiment fills.
TP/SL are software checks at workflow runs, NOT standing bracket orders.
Coinbase closed candles produce signals; fresh Alpaca quotes price decisions.
Fees can post later. P&L below is before USD fees; no fabricated net performance.

## Entry diagnostics

Candidates: 0. Skipped: 0. Broker order results: 0.
Broker order results are not proof of fills; see orders.csv.

Entries paused: entry_scan_interval_not_elapsed.


Per-candidate decisions: entry_decisions.csv. Quotes checked for entries: quotes.csv.

## Open / pending positions

| Coin | Bar | Strategy | Entry | Filled qty | Entry dollars | Remaining | TP | SL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTC/USD | 1h | trend_pullback | 81141.525053225 | 0.002465863 | 200.08388439232058 | 0.002459697 | 82340.13793842054 | 80542.21861062724 | open |
| ETH/USD | 1h | trend_pullback | 2355.8 | 0.084922083 | 200.0594431314 | 0.084709777 | 2403.3986052917962 | 2332.000697354102 | open |
| SOL/USD | 1h | trend_pullback | 102.297 | 1.955034213 | 199.994134887261 | 1.950146627 | 104.62114764381133 | 101.13492617809433 | open |
## Closed cycles

| Coin | Bar | Strategy | Entry | Filled qty | Entry dollars | Remaining | TP | SL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ETH/USD | 15m | trend_pullback | 2352.83 | 0.08501594 | 200.0280541102 | 0.0 | 2368.832612413611 | 2344.8286937931944 | closed |
| SOL/USD | 5m | trend_pullback | 102.0 | 1.962246379 | 200.149130658 | 0.0 | 102.407696 | 101.796152 | closed |

Order IDs, fill prices/times and quantities: orders.csv.
Closed trade cashflows: closed_trades.csv. Broker-reported fees: fees.csv.
Dust is kept in the ledger; it is not silently written off or counted as a win.

## Reconciliation

Status: fee_pending
New entries blocked: False
Exit checks allowed: True
Accounting final: False

| Coin | Expected | Broker | Difference | Unconfirmed |
| --- | --- | --- | --- | --- |
| BTCUSD | 0.002465863 | 0.002459697 | -0.000006166 | 0.000006166 |
| ETHUSD | 0.084922083 | 0.084709777 | -0.000212306 | 0.000212306 |
| SOLUSD | 1.959939829 | 1.950146627 | -0.009793202 | 0.009793202 |

PENDING, NOT CONFIRMED: fee-sized shortfall. No fee record invented.
New buys permitted by explicit paper policy; all entry checks still apply.
Guarded software exits remain active. Trade accounting is provisional until broker records reconcile.

Entry scan status: not_due
Next entry scan eligible: 2026-10-28T21:23:38+00:00
Entry scans: at most once every 30 minutes. Software exits: every successful workflow tick, not standing orders.
Full diagnostics: reconciliation.csv and reconciliation.json.

## Discovery watchlist

Last refresh: 2026-10-28T20:53:39+00:00
Source status: partial
Selected: AVAX/USD, BTC/USD, ETH/USD, LINK/USD, LTC/USD, SOL/USD, PEPE/USD, ARB/USD, BCH/USD, AAVE/USD
Emerging momentum is a screening label, not an undervaluation or profit claim.
News is attention/risk context, not a buy signal. Existing strategy, quote and risk checks still apply.
USD volume is estimated from Coinbase base volume times last price, not broker liquidity.
Details, exclusions, source errors and headline links: watchlist.json and watchlist.csv.
