# Alpaca crypto PAPER bot

Status: FAILED_CLOSED
Dedicated paper account only. Broker fills, not virtual experiment fills.
TP/SL are software checks at workflow runs, NOT standing bracket orders.
Coinbase closed candles produce signals; fresh Alpaca quotes price decisions.
Fees can post later. P&L below is before USD fees; no fabricated net performance.

Reason: Position/fee reconciliation mismatch for AAVEUSD: expected=1.490616996, broker=1.472216072, difference=-0.018400924, recorded_fee_quantity=0; AVAXUSD: expected=0.114837798, broker=0, difference=-0.114837798, recorded_fee_quantity=-0.056598413; BTCUSD: expected=0.002574582, broker=0.002542525, difference=-0.000032057, recorded_fee_quantity=-0.000012395; ETHUSD: expected=0.088078742, broker=0.087198248, difference=-0.000880494, recorded_fee_quantity=-0.000641803; LINKUSD: expected=17.716411239, broker=17.58638928, difference=-0.130021959, recorded_fee_quantity=-0.042194093; SOLUSD: expected=0.015897999, broker=0, difference=-0.015897999, recorded_fee_quantity=-0.024677697; TRUMPUSD: expected=118.356665968, broker=117.76859504, difference=-0.588070928, recorded_fee_quantity=0; UNIUSD: expected=28.090044610, broker=27.812630697, difference=-0.277413913, recorded_fee_quantity=-0.069003589; unresolved after read-only retries; entries and exits blocked

## Entry diagnostics

Candidates: 3. Skipped: 1. Broker order results: 1.
Broker order results are not proof of fills; see orders.csv.

| Coin | Bar | Strategy | Outcome | Reason | Details |
| --- | --- | --- | --- | --- | --- |
| UNI/USD | 5m | trend_pullback | skipped | symbol_already_active | {} |
| BTC/USD | 5m | trend_pullback | order_result | broker_order_returned | {"broker_order_id": "32d67e3d-2ecc-4b00-aeb9-63780854d925", "broker_status": "pending_new", "client_order_id": "csl2-6a68a154fbb6606d56da1a3545e2807a", "quantity": "0.002548899", "reference_ask": 78465.231} |

Per-candidate decisions: entry_decisions.csv. Quotes checked for entries: quotes.csv.

## Data errors

| Coin | Bar | Stage | Error type |
| --- | --- | --- | --- |
| AAVE/USD | 5m | candles | ValueError |
| TRUMP/USD | 5m | candles | ValueError |

## Open / pending positions

| Coin | Bar | Strategy | Entry | Filled qty | Entry dollars | Remaining | TP | SL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TRUMP/USD | 1h | rolling_vwap_reclaim | 1.6931 | 118.063754427 | 199.89374262035372 | 117.76859504 | 1.7820998552547356 | 1.6486000723726324 | open |
| LINK/USD | 1h | bollinger_reversion | 11.351 | 17.630465444 | 200.123413254844 | 17.58638928 | 11.639403080819955 | 11.206798459590024 | open |
| UNI/USD | 1h | trend_pullback | 7.1791 | 27.882336539 | 200.1700822471349 | 27.812630697 | 7.42161978344981 | 7.057840108275095 | open |
| ETH/USD | 15m | donchian_breakout | 2288.24 | 0.08741679 | 200.03059554959998 | 0.087198248 | 2311.5322058677275 | 2276.593897066136 | open |
| AAVE/USD | 1h | trend_pullback | 135.566 | 1.475905837 | 200.08265069874201 | 1.472216072 | 139.92848587099192 | 133.38475706450404 | open |
| BTC/USD | 5m | trend_pullback | n/a | n/a | n/a | 0.0 | n/a | n/a | pending |
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
| ETH/USD | 1h | bollinger_reversion | 2305.2 | 0.086782579 | 200.05120111079998 | 0.0 | 2359.320736026376 | 2278.1396319868118 | closed |
| DOT/USD | 15m | rsi_rebound | 0.9702 | 206.185779572 | 200.0414433407544 | 0.0 | 0.9933076118532437 | 0.958646194073378 | closed |
| SOL/USD | 15m | rsi_rebound | 100.121 | 1.997443272 | 199.98601783591198 | 0.0 | 101.35444207935545 | 99.50427896032227 | closed |
| BTC/USD | 1h | bollinger_reversion | 80283.540728391 | 0.002491328 | 200.0126329557809 | 0.0 | 81609.51263608344 | 79620.55477454478 | closed |
| PEPE/USD | 15m | trend_pullback | 5.09e-06 | 38241304.50980393 | 194.648239954902 | 0.0 | 5.32158489621366e-06 | 4.9742075518931705e-06 | closed |
| AVAX/USD | 5m | donchian_breakout | 8.818 | 22.639365101 | 199.63392146061798 | 0.0 | 8.890288014191333 | 8.781855992904333 | closed |
| HYPE/USD | 15m | ema_cross | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| HYPE/USD | 15m | donchian_breakout | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| ARB/USD | 15m | ema_cross | 0.17032 | 1174.398120963 | 200.0234879624182 | 0.0 | 0.1737328821130826 | 0.1686135589434587 | closed |
| FIL/USD | 15m | donchian_breakout | 0.9095 | 219.884121068 | 199.984608111346 | 0.0 | 0.9260077902125277 | 0.9012461048937361 | closed |
| HYPE/USD | 1h | donchian_breakout | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| PEPE/USD | 5m | bollinger_reversion | 4.86e-06 | 41237113.40206186 | 200.41237113402062 | 0.0 | 4.947608994219858e-06 | 4.816195502890071e-06 | closed |
| SOL/USD | 5m | donchian_breakout | 101.96 | 1.961938395 | 200.0392387542 | 0.0 | 102.8022141789213 | 101.53889291053935 | closed |
| PEPE/USD | 1h | trend_pullback | 5.03e-06 | 38668482.10735587 | 194.50246500000003 | 0.0 | 5.424840282494075e-06 | 4.832579858752963e-06 | closed |
| HYPE/USD | 15m | donchian_breakout | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| HYPE/USD | 5m | bollinger_reversion | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| SOL/USD | 5m | rsi_rebound | 100.3 | 1.994415636 | 200.0398882908 | 0.0 | 101.01718373799453 | 99.94140813100273 | closed |
| AAVE/USD | 15m | trend_pullback | 134.489 | 1.487541837 | 200.058014116293 | 0.0 | 136.09900983532222 | 133.6839950823389 | closed |
| AVAX/USD | 15m | bollinger_reversion | 8.528 | 23.415639305 | 199.68857199304 | 0.0 | 8.594000202002652 | 8.494999898998675 | closed |
| LINK/USD | 5m | bollinger_reversion | 11.5471 | 17.328019407 | 200.0883728945697 | 0.0 | 11.613289919548077 | 11.514005040225962 | closed |
| ETH/USD | 5m | macd_momentum | 2267.56 | 0.088206756 | 200.01411163536 | 0.0 | 2276.6295999999998 | 2263.0252 | closed |
| AAVE/USD | 15m | donchian_breakout | 138.6 | 1.444147591 | 200.15885611259998 | 0.0 | 140.91959811562253 | 137.44020094218874 | closed |
| BTC/USD | 15m | trend_pullback | 77738.296008397 | 0.002574304 | 200.12200636760042 | 0.0 | 78049.059568397 | 77582.914228397 | closed |
| AVAX/USD | 15m | donchian_breakout | 8.872 | 22.519479349 | 199.792820784328 | 0.0 | 9.01437007758712 | 8.80081496120644 | closed |
| UNI/USD | 15m | trend_pullback | 7.181 | 27.90492457 | 200.38526333717 | 0.0 | 7.300773753751183 | 7.121113123124409 | closed |
| ETH/USD | 15m | trend_pullback | 2268.6 | 0.088187309 | 200.0617291974 | 0.0 | 2279.9521028114164 | 2262.9239485942917 | closed |
| HYPE/USD | 5m | trend_pullback | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| LINK/USD | 5m | trend_pullback | 11.7339 | 17.05029838 | 200.06649616108203 | 0.0 | 11.805452540737084 | 11.698123729631458 | closed |
| AAVE/USD | 15m | trend_pullback | 137.614 | 1.454545454 | 200.165818106756 | 0.0 | 139.66480060462044 | 136.58859969768977 | closed |
| BTC/USD | 5m | bollinger_reversion | 77777.084288058 | 0.00257212 | 200.05199403899974 | 0.0 | 78088.111700058 | 77621.570582058 | closed |
| UNI/USD | 5m | bollinger_reversion | 7.205 | 27.773534598 | 200.10831677859002 | 0.0 | 7.270419269591361 | 7.1722903652043195 | closed |
| ETH/USD | 15m | trend_pullback | 2264.065049526 | 0.08838607 | 200.11181195195852 | 0.0 | 2276.8293182366338 | 2257.6829151706834 | closed |
| BTC/USD | 15m | macd_momentum | 77940.6 | 0.002567047 | 200.0771834082 | 0.0 | 78276.92160587902 | 77772.43919706049 | closed |
| UNI/USD | 1h | donchian_breakout | 7.3045 | 27.404768429 | 200.17813098963052 | 0.0 | 7.549550005739403 | 7.181974997130299 | closed |
| SOL/USD | 1h | bollinger_reversion | 94.885 | 2.107477118 | 199.96796634142999 | 0.0 | 96.44891526039979 | 94.10304236980012 | closed |
| TRUMP/USD | 1h | donchian_breakout | 1.70826 | 117.164616285 | 200.14762741501409 | 0.0 | 1.7793160226095484 | 1.6727319886952257 | closed |
| AAVE/USD | 15m | bollinger_reversion | 133.552 | 1.498228344 | 200.09139179788798 | 0.0 | 135.68555812265961 | 132.48522093867018 | closed |
| SOL/USD | 1h | bollinger_reversion | 94.3207 | 2.121115706 | 200.0651181709142 | 0.0 | 95.86473168713084 | 93.54868415643458 | closed |
| SOL/USD | 15m | bollinger_reversion | 93.89 | 2.130606157 | 200.04261208072998 | 0.0 | 94.82614521801622 | 93.42192739099188 | closed |
| BTC/USD | 15m | ema_cross | 78236.044797716 | 0.0025569 | 200.04174294328 | 0.0 | 78682.87850149203 | 78012.62794582798 | closed |

Order IDs, fill prices/times and quantities: orders.csv.
Closed trade cashflows: closed_trades.csv. Broker-reported fees: fees.csv.
Dust is kept in the ledger; it is not silently written off or counted as a win.

## Reconciliation

Status: mismatch
New entries blocked: True
Exit checks allowed: False
Accounting final: False

| Coin | Expected | Broker | Difference | Unconfirmed |
| --- | --- | --- | --- | --- |
| AAVEUSD | 1.490616996 | 1.472216072 | -0.018400924 | 0 |
| ARBUSD | 0E-9 | 0 | 0E-9 | 0 |
| AVAXUSD | 0.114837798 | 0 | -0.114837798 | 0 |
| BTCUSD | 0.002574582 | 0.002542525 | -0.000032057 | 0 |
| DOTUSD | 0E-9 | 0 | 0E-9 | 0 |
| ETHUSD | 0.088078742 | 0.087198248 | -0.000880494 | 0 |
| FILUSD | 0E-9 | 0 | 0E-9 | 0 |
| HYPEUSD | 0 | 0 | 0 | 0 |
| LINKUSD | 17.716411239 | 17.58638928 | -0.130021959 | 0 |
| PEPEUSD | 0E-9 | 0 | 0E-9 | 0 |
| SOLUSD | 0.015897999 | 0 | -0.015897999 | 0 |
| TRUMPUSD | 118.356665968 | 117.76859504 | -0.588070928 | 0 |
| UNIUSD | 28.090044610 | 27.812630697 | -0.277413913 | 0 |

UNRESOLVED: entries and automated exits blocked. Review the paper holding.

Entry scan status: completed_with_data_errors
Next entry scan eligible: 2026-11-02T03:42:48+00:00
Entry scans: at most once every 30 minutes. Software exits: every successful workflow tick, not standing orders.
Full diagnostics: reconciliation.csv and reconciliation.json.

## Discovery watchlist

Last refresh: 2026-11-02T03:12:49+00:00
Source status: partial
Selected: AAVE/USD, ETH/USD, LINK/USD, TRUMP/USD, UNI/USD, AVAX/USD, BTC/USD, LTC/USD, SOL/USD
Emerging momentum is a screening label, not an undervaluation or profit claim.
News is attention/risk context, not a buy signal. Existing strategy, quote and risk checks still apply.
USD volume is estimated from Coinbase base volume times last price, not broker liquidity.
Details, exclusions, source errors and headline links: watchlist.json and watchlist.csv.
