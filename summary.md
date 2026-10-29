# Alpaca crypto PAPER bot

Status: PAPER_TICK_COMPLETED
Dedicated paper account only. Broker fills, not virtual experiment fills.
TP/SL are software checks at workflow runs, NOT standing bracket orders.
Coinbase closed candles produce signals; fresh Alpaca quotes price decisions.
Fees can post later. P&L below is before USD fees; no fabricated net performance.

## Entry diagnostics

Candidates: 8. Skipped: 6. Broker order results: 2.
Broker order results are not proof of fills; see orders.csv.

| Coin | Bar | Strategy | Outcome | Reason | Details |
| --- | --- | --- | --- | --- | --- |
| SOL/USD | 1h | bollinger_reversion | skipped | symbol_already_active | {} |
| AVAX/USD | 1h | bollinger_reversion | skipped | no_fresh_quote | {"max_quote_age_seconds": 30} |
| AVAX/USD | 1h | rsi_rebound | skipped | no_fresh_quote | {"max_quote_age_seconds": 30} |
| BTC/USD | 1h | bollinger_reversion | order_result | broker_order_returned | {"broker_order_id": "de618564-ef84-4ea7-b5dc-f70d6065d7bd", "broker_status": "pending_new", "client_order_id": "csl2-cda9918a3e56b6b2708aa959ec7d371a", "quantity": "0.002491328", "reference_ask": 80278.455} |
| PEPE/USD | 15m | trend_pullback | order_result | broker_order_returned | {"broker_order_id": "f0cb3e7a-f313-4c0c-8c96-776b08dca4d9", "broker_status": "pending_new", "client_order_id": "csl2-c48b36af55f32fd5320bd72230a2142a", "quantity": "38241304.50980393", "reference_ask": 5.1e-06} |
| PEPE/USD | 1h | trend_pullback | skipped | symbol_already_active | {} |
| BCH/USD | 1h | bollinger_reversion | skipped | max_positions | {"active_positions": 6, "max_positions": 6} |
| BCH/USD | 1h | rsi_rebound | skipped | max_positions | {"active_positions": 6, "max_positions": 6} |

Per-candidate decisions: entry_decisions.csv. Quotes checked for entries: quotes.csv.

## Open / pending positions

| Coin | Bar | Strategy | Entry | Filled qty | Entry dollars | Remaining | TP | SL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ARB/USD | 15m | bollinger_reversion | 0.16432 | 1217.433649866 | 200.0486973459811 | 1214.390065741 | 0.16884034877884005 | 0.16205982561057997 | open |
| ETH/USD | 1h | bollinger_reversion | 2305.2 | 0.086782579 | 200.05120111079998 | 0.086565622 | 2359.320736026376 | 2278.1396319868118 | open |
| DOT/USD | 15m | rsi_rebound | 0.9702 | 206.185779572 | 200.0414433407544 | 205.670315123 | 0.9933076118532437 | 0.958646194073378 | open |
| SOL/USD | 15m | rsi_rebound | 100.121 | 1.997443272 | 199.98601783591198 | 1.992449663 | 101.35444207935545 | 99.50427896032227 | open |
| BTC/USD | 1h | bollinger_reversion | 80283.540728391 | 0.002491328 | 200.0126329557809 | 0.002485099 | 81609.51263608344 | 79620.55477454478 | open |
| PEPE/USD | 15m | trend_pullback | 5.09e-06 | 38241304.50980393 | 194.648239954902 | 38145701.24852942 | 5.32158489621366e-06 | 4.9742075518931705e-06 | open |
## Closed cycles

| Coin | Bar | Strategy | Entry | Filled qty | Entry dollars | Remaining | TP | SL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ETH/USD | 15m | trend_pullback | 2352.83 | 0.08501594 | 200.0280541102 | 0.0 | 2368.832612413611 | 2344.8286937931944 | closed |
| SOL/USD | 5m | trend_pullback | 102.0 | 1.962246379 | 200.149130658 | 0.0 | 102.407696 | 101.796152 | closed |
| BTC/USD | 1h | trend_pullback | 81141.525053225 | 0.002465863 | 200.08388439232058 | 0.0 | 82340.13793842054 | 80542.21861062724 | closed |
| ETH/USD | 1h | trend_pullback | 2355.8 | 0.084922083 | 200.0594431314 | 0.0 | 2403.3986052917962 | 2332.000697354102 | closed |
| SOL/USD | 1h | trend_pullback | 102.297 | 1.955034213 | 199.994134887261 | 0.0 | 104.62114764381133 | 101.13492617809433 | closed |
| LINK/USD | 1h | macd_momentum | 11.85 | 16.87763713 | 199.9999999905 | 0.0 | 12.243345161382472 | 11.653327419308763 | closed |
| ARB/USD | 1h | donchian_breakout | 0.176896 | 1129.969038848 | 199.88700309605582 | 0.0 | 0.1847036898550324 | 0.17299215507248378 | closed |
| PEPE/USD | 5m | trend_pullback | 5.04e-06 | 39682539.68253968 | 199.99999999999997 | 0.0 | 5.161466000949713e-06 | 4.979266999525144e-06 | closed |
| UNI/USD | 5m | trend_pullback | 7.248 | 27.601435274 | 200.055202865952 | 0.0 | 7.315980677349064 | 7.214009661325468 | closed |
| PEPE/USD | 5m | trend_pullback | 5.04e-06 | 39761431.411530815 | 200.39761431411532 | 0.0 | 5.137478146438155e-06 | 4.991260926780923e-06 | closed |
| PEPE/USD | 5m | bollinger_reversion | 4.88e-06 | 40899795.501022495 | 199.59100204498978 | 0.0 | 5.0278268626405795e-06 | 4.80608656867971e-06 | closed |

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
| ARBUSD | 1220.258572464 | 1214.390065741 | -5.868506723 | 5.868506723 |
| BTCUSD | 0.002497494 | 0.002485099 | -0.000012395 | 0.000012395 |
| DOTUSD | 206.185779572 | 205.670315123 | -0.515464449 | 0.515464449 |
| ETHUSD | 0.086994885 | 0.086565622 | -0.000429263 | 0.000429263 |
| LINKUSD | 0.042194093 | 0 | -0.042194093 | 0.042194093 |
| PEPEUSD | 38542163.926291665 | 38145701.24852942 | -396462.677762245 | 396462.677762245 |
| SOLUSD | 2.007236474 | 1.992449663 | -0.014786811 | 0.014786811 |
| UNIUSD | 0.069003589 | 0 | -0.069003589 | 0.069003589 |

PENDING, NOT CONFIRMED: fee-sized shortfall. No fee record invented.
New buys permitted by explicit paper policy; all entry checks still apply.
Guarded software exits remain active. Trade accounting is provisional until broker records reconcile.

Entry scan status: completed
Next entry scan eligible: 2026-10-29T05:58:02+00:00
Entry scans: at most once every 30 minutes. Software exits: every successful workflow tick, not standing orders.
Full diagnostics: reconciliation.csv and reconciliation.json.

## Discovery watchlist

Last refresh: 2026-10-29T05:28:04+00:00
Source status: partial
Selected: ARB/USD, DOT/USD, ETH/USD, SOL/USD, AVAX/USD, BTC/USD, LINK/USD, LTC/USD, PEPE/USD, BCH/USD
Emerging momentum is a screening label, not an undervaluation or profit claim.
News is attention/risk context, not a buy signal. Existing strategy, quote and risk checks still apply.
USD volume is estimated from Coinbase base volume times last price, not broker liquidity.
Details, exclusions, source errors and headline links: watchlist.json and watchlist.csv.
