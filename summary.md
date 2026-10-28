# Alpaca crypto PAPER bot

Status: PAPER_TICK_COMPLETED
Dedicated paper account only. Broker fills, not virtual experiment fills.
TP/SL are software checks at workflow runs, NOT standing bracket orders.
Coinbase closed candles produce signals; fresh Alpaca quotes price decisions.
Fees can post later. P&L below is before USD fees; no fabricated net performance.

## Entry diagnostics

Candidates: 8. Skipped: 7. Broker order results: 1.
Broker order results are not proof of fills; see orders.csv.

| Coin | Bar | Strategy | Outcome | Reason | Details |
| --- | --- | --- | --- | --- | --- |
| BTC/USD | 5m | trend_pullback | skipped | symbol_already_active | {} |
| ETH/USD | 5m | trend_pullback | skipped | symbol_already_active | {} |
| ETH/USD | 5m | rolling_vwap_reclaim | skipped | symbol_already_active | {} |
| LINK/USD | 5m | trend_pullback | skipped | symbol_already_active | {} |
| SOL/USD | 5m | trend_pullback | skipped | symbol_already_active | {} |
| SOL/USD | 5m | rolling_vwap_reclaim | skipped | symbol_already_active | {} |
| AVAX/USD | 5m | trend_pullback | skipped | no_fresh_quote | {"max_quote_age_seconds": 30} |
| PEPE/USD | 5m | trend_pullback | order_result | broker_order_returned | {"broker_order_id": "295641db-7e3f-4ad6-b747-7b95590fae00", "broker_status": "pending_new", "client_order_id": "csl2-84b898b923e391ae39a551126f9dd068", "quantity": "39682539.68253968", "reference_ask": 5.04e-06} |

Per-candidate decisions: entry_decisions.csv. Quotes checked for entries: quotes.csv.

## Data errors

| Coin | Bar | Stage | Error type |
| --- | --- | --- | --- |
| ARB/USD | 5m | candles | ValueError |
| AAVE/USD | 5m | candles | ValueError |

## Open / pending positions

| Coin | Bar | Strategy | Entry | Filled qty | Entry dollars | Remaining | TP | SL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTC/USD | 1h | trend_pullback | 81141.525053225 | 0.002465863 | 200.08388439232058 | 0.002459697 | 82340.13793842054 | 80542.21861062724 | open |
| ETH/USD | 1h | trend_pullback | 2355.8 | 0.084922083 | 200.0594431314 | 0.084709777 | 2403.3986052917962 | 2332.000697354102 | open |
| SOL/USD | 1h | trend_pullback | 102.297 | 1.955034213 | 199.994134887261 | 1.950146627 | 104.62114764381133 | 101.13492617809433 | open |
| LINK/USD | 1h | macd_momentum | 11.85 | 16.87763713 | 199.9999999905 | 16.835443037 | 12.243345161382472 | 11.653327419308763 | open |
| ARB/USD | 1h | donchian_breakout | 0.176896 | 1129.969038848 | 199.88700309605582 | 1127.14411625 | 0.1847036898550324 | 0.17299215507248378 | open |
| PEPE/USD | 5m | trend_pullback | 5.04e-06 | 39682539.68253968 | 199.99999999999997 | 39583333.33333333 | 5.161466000949713e-06 | 4.979266999525144e-06 | open |
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
| ARBUSD | 1129.969038848 | 1127.14411625 | -2.824922598 | 2.824922598 |
| BTCUSD | 0.002465863 | 0.002459697 | -0.000006166 | 0.000006166 |
| ETHUSD | 0.084922083 | 0.084709777 | -0.000212306 | 0.000212306 |
| LINKUSD | 16.87763713 | 16.835443037 | -0.042194093 | 0.042194093 |
| PEPEUSD | 39682539.68253968 | 39583333.33333333 | -99206.34920635 | 99206.34920635 |
| SOLUSD | 1.959939829 | 1.950146627 | -0.009793202 | 0.009793202 |

PENDING, NOT CONFIRMED: fee-sized shortfall. No fee record invented.
New buys permitted by explicit paper policy; all entry checks still apply.
Guarded software exits remain active. Trade accounting is provisional until broker records reconcile.

Entry scan status: completed_with_data_errors
Next entry scan eligible: 2026-10-28T23:09:03+00:00
Entry scans: at most once every 30 minutes. Software exits: every successful workflow tick, not standing orders.
Full diagnostics: reconciliation.csv and reconciliation.json.

## Discovery watchlist

Last refresh: 2026-10-28T22:39:05+00:00
Source status: partial
Selected: ARB/USD, BTC/USD, ETH/USD, LINK/USD, SOL/USD, AVAX/USD, LTC/USD, PEPE/USD, BCH/USD, AAVE/USD
Emerging momentum is a screening label, not an undervaluation or profit claim.
News is attention/risk context, not a buy signal. Existing strategy, quote and risk checks still apply.
USD volume is estimated from Coinbase base volume times last price, not broker liquidity.
Details, exclusions, source errors and headline links: watchlist.json and watchlist.csv.
