# Alpaca crypto PAPER bot

Status: PAPER_TICK_COMPLETED
Dedicated paper account only. Broker fills, not virtual experiment fills.
TP/SL are software checks at workflow runs, NOT standing bracket orders.
Coinbase closed candles produce signals; fresh Alpaca quotes price decisions.
Fees can post later. P&L below is before USD fees; no fabricated net performance.

## Entry diagnostics

Candidates: 15. Skipped: 14. Broker order results: 1.
Broker order results are not proof of fills; see orders.csv.

| Coin | Bar | Strategy | Outcome | Reason | Details |
| --- | --- | --- | --- | --- | --- |
| ARB/USD | 1h | ema_cross | skipped | symbol_already_active | {} |
| PEPE/USD | 15m | donchian_breakout | skipped | symbol_already_active | {} |
| PEPE/USD | 1h | donchian_breakout | skipped | symbol_already_active | {} |
| PEPE/USD | 1h | macd_momentum | skipped | symbol_already_active | {} |
| AVAX/USD | 15m | donchian_breakout | skipped | spread_too_wide | {"max_spread_bps": 50, "spread_bps": 60.68922431585098} |
| LTC/USD | 15m | donchian_breakout | skipped | spread_too_wide | {"max_spread_bps": 50, "spread_bps": 62.269067015779434} |
| LTC/USD | 15m | squeeze_breakout | skipped | spread_too_wide | {"max_spread_bps": 50, "spread_bps": 62.269067015779434} |
| LTC/USD | 1h | trend_pullback | skipped | spread_too_wide | {"max_spread_bps": 50, "spread_bps": 62.269067015779434} |
| LTC/USD | 1h | macd_momentum | skipped | spread_too_wide | {"max_spread_bps": 50, "spread_bps": 62.269067015779434} |
| HYPE/USD | 15m | donchian_breakout | order_result | broker_order_returned | {"broker_order_id": "6e2338c1-b328-46d3-959d-f1e2056ab203", "broker_status": "pending_new", "client_order_id": "csl2-c85038d0825c6862a3a66dc178f9b1a2", "quantity": "1.891298999", "reference_ask": 96.007} |
| HYPE/USD | 1h | donchian_breakout | skipped | symbol_already_active | {} |
| HYPE/USD | 6h | ema_cross | skipped | already_seen | {} |
| HYPE/USD | 6h | donchian_breakout | skipped | already_seen | {} |
| UNI/USD | 15m | donchian_breakout | skipped | max_positions | {"active_positions": 6, "max_positions": 6} |
| UNI/USD | 1h | donchian_breakout | skipped | max_positions | {"active_positions": 6, "max_positions": 6} |

Per-candidate decisions: entry_decisions.csv. Quotes checked for entries: quotes.csv.

## Data errors

| Coin | Bar | Stage | Error type |
| --- | --- | --- | --- |
| ARB/USD | 5m | candles | ValueError |
| FIL/USD | 5m | candles | ValueError |
| LINK/USD | 5m | candles | ValueError |

## Open / pending positions

| Coin | Bar | Strategy | Entry | Filled qty | Entry dollars | Remaining | TP | SL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ETH/USD | 1h | bollinger_reversion | 2305.2 | 0.086782579 | 200.05120111079998 | 0.086565622 | 2359.320736026376 | 2278.1396319868118 | open |
| BTC/USD | 1h | bollinger_reversion | 80283.540728391 | 0.002491328 | 200.0126329557809 | 0.002485099 | 81609.51263608344 | 79620.55477454478 | open |
| ARB/USD | 15m | ema_cross | 0.17032 | 1174.398120963 | 200.0234879624182 | 1171.46212566 | 0.1737328821130826 | 0.1686135589434587 | open |
| FIL/USD | 15m | donchian_breakout | 0.9095 | 219.884121068 | 199.984608111346 | 219.334410765 | 0.9260077902125277 | 0.9012461048937361 | open |
| PEPE/USD | 1h | trend_pullback | 5.03e-06 | 38668482.10735587 | 194.50246500000003 | 38571810.90208748 | 5.424840282494075e-06 | 4.832579858752963e-06 | open |
| HYPE/USD | 15m | donchian_breakout | n/a | n/a | n/a | 0.0 | n/a | n/a | pending |
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
| ARB/USD | 15m | bollinger_reversion | 0.16432 | 1217.433649866 | 200.0486973459811 | 0.0 | 0.16884034877884005 | 0.16205982561057997 | closed |
| DOT/USD | 15m | rsi_rebound | 0.9702 | 206.185779572 | 200.0414433407544 | 0.0 | 0.9933076118532437 | 0.958646194073378 | closed |
| SOL/USD | 15m | rsi_rebound | 100.121 | 1.997443272 | 199.98601783591198 | 0.0 | 101.35444207935545 | 99.50427896032227 | closed |
| PEPE/USD | 15m | trend_pullback | 5.09e-06 | 38241304.50980393 | 194.648239954902 | 0.0 | 5.32158489621366e-06 | 4.9742075518931705e-06 | closed |
| AVAX/USD | 5m | donchian_breakout | 8.818 | 22.639365101 | 199.63392146061798 | 0.0 | 8.890288014191333 | 8.781855992904333 | closed |
| HYPE/USD | 15m | ema_cross | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| HYPE/USD | 15m | donchian_breakout | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| HYPE/USD | 1h | donchian_breakout | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| PEPE/USD | 5m | bollinger_reversion | 4.86e-06 | 41237113.40206186 | 200.41237113402062 | 0.0 | 4.947608994219858e-06 | 4.816195502890071e-06 | closed |
| SOL/USD | 5m | donchian_breakout | 101.96 | 1.961938395 | 200.0392387542 | 0.0 | 102.8022141789213 | 101.53889291053935 | closed |

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
| ARBUSD | 1174.398120963 | 1171.46212566 | -2.935995303 | 2.935995303 |
| AVAXUSD | 0.056598413 | 0 | -0.056598413 | 0.056598413 |
| BTCUSD | 0.002485099 | 0.002485099 | 0E-9 | 0 |
| DOTUSD | 0E-9 | 0 | 0E-9 | 0 |
| ETHUSD | 0.086565622 | 0.086565622 | 0E-9 | 0 |
| FILUSD | 219.884121068 | 219.334410765 | -0.549710303 | 0.549710303 |
| HYPEUSD | 0 | 0 | 0 | 0 |
| LINKUSD | 0E-9 | 0 | 0E-9 | 0 |
| PEPEUSD | 38771574.890861025 | 38571810.90208748 | -199763.988773545 | 199763.988773545 |
| SOLUSD | 0.004904846 | 0 | -0.004904846 | 0.004904846 |
| UNIUSD | 0E-9 | 0 | 0E-9 | 0 |

PENDING, NOT CONFIRMED: fee-sized shortfall. No fee record invented.
New buys permitted by explicit paper policy; all entry checks still apply.
Guarded software exits remain active. Trade accounting is provisional until broker records reconcile.

Entry scan status: completed_with_data_errors
Next entry scan eligible: 2026-10-29T16:51:22+00:00
Entry scans: at most once every 30 minutes. Software exits: every successful workflow tick, not standing orders.
Full diagnostics: reconciliation.csv and reconciliation.json.

## Discovery watchlist

Last refresh: 2026-10-29T16:21:25+00:00
Source status: partial
Selected: ARB/USD, BTC/USD, ETH/USD, FIL/USD, PEPE/USD, AVAX/USD, LINK/USD, LTC/USD, SOL/USD, HYPE/USD, UNI/USD
Emerging momentum is a screening label, not an undervaluation or profit claim.
News is attention/risk context, not a buy signal. Existing strategy, quote and risk checks still apply.
USD volume is estimated from Coinbase base volume times last price, not broker liquidity.
Details, exclusions, source errors and headline links: watchlist.json and watchlist.csv.
