# Alpaca crypto PAPER bot

Status: PAPER_TICK_COMPLETED
Dedicated paper account only. Broker fills, not virtual experiment fills.
TP/SL are software checks at workflow runs, NOT standing bracket orders.
Coinbase closed candles produce signals; fresh Alpaca quotes price decisions.
Fees can post later. P&L below is before USD fees; no fabricated net performance.

## Entry diagnostics

Candidates: 4. Skipped: 4. Broker order results: 0.
Broker order results are not proof of fills; see orders.csv.

| Coin | Bar | Strategy | Outcome | Reason | Details |
| --- | --- | --- | --- | --- | --- |
| ETH/USD | 15m | trend_pullback | skipped | symbol_already_active | {} |
| ETH/USD | 15m | macd_momentum | skipped | symbol_already_active | {} |
| SOL/USD | 5m | trend_pullback | skipped | max_positions | {"active_positions": 6, "max_positions": 6} |
| BCH/USD | 5m | rolling_vwap_reclaim | skipped | max_positions | {"active_positions": 6, "max_positions": 6} |

Per-candidate decisions: entry_decisions.csv. Quotes checked for entries: quotes.csv.

## Data errors

| Coin | Bar | Stage | Error type |
| --- | --- | --- | --- |
| ARB/USD | 5m | candles | ValueError |
| PEPE/USD | 5m | candles | ValueError |
| RENDER/USD | 5m | candles | ValueError |

## Open / pending positions

| Coin | Bar | Strategy | Entry | Filled qty | Entry dollars | Remaining | TP | SL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PEPE/USD | 1h | macd_momentum | 5.01e-06 | 39920159.68063872 | 200.00000000000003 | 39820359.28143712 | 5.263353097673113e-06 | 4.8833234511634434e-06 | open |
| BTC/USD | 1h | donchian_breakout | 80600.909 | 0.00248268 | 200.10626475612 | 0.002476473 | 82524.74630170345 | 79638.99034914827 | open |
| ETH/USD | 1h | donchian_breakout | 2441.927 | 0.077328403 | 188.83031515258102 | 0.077135081 | 2517.287691655622 | 2404.246654172189 | open |
| LINK/USD | 15m | trend_pullback | 11.477331943 | 17.404925593 | 199.7621084740771 | 17.361413279 | 11.667372015496435 | 11.38231190675178 | open |
| RENDER/USD | 15m | trend_pullback | 1.6069 | 124.428407005 | 199.94400721633448 | 124.117335987 | 1.6389355580017448 | 1.5908822209991276 | open |
| ARB/USD | 15m | trend_pullback | 0.16392 | 1221.001221001 | 200.14652014648394 | 1217.948717948 | 0.16669779274923682 | 0.1625311036253816 | open |
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
| TRUMP/USD | 1h | rolling_vwap_reclaim | 1.6931 | 118.063754427 | 199.89374262035372 | 0.0 | 1.7820998552547356 | 1.6486000723726324 | closed |
| AAVE/USD | 15m | bollinger_reversion | 133.552 | 1.498228344 | 200.09139179788798 | 0.0 | 135.68555812265961 | 132.48522093867018 | closed |
| LINK/USD | 1h | bollinger_reversion | 11.351 | 17.630465444 | 200.123413254844 | 0.0 | 11.639403080819955 | 11.206798459590024 | closed |
| SOL/USD | 1h | bollinger_reversion | 94.3207 | 2.121115706 | 200.0651181709142 | 0.0 | 95.86473168713084 | 93.54868415643458 | closed |
| UNI/USD | 1h | trend_pullback | 7.1791 | 27.882336539 | 200.1700822471349 | 0.0 | 7.42161978344981 | 7.057840108275095 | closed |
| SOL/USD | 15m | bollinger_reversion | 93.89 | 2.130606157 | 200.04261208072998 | 0.0 | 94.82614521801622 | 93.42192739099188 | closed |
| BTC/USD | 15m | ema_cross | 78236.044797716 | 0.0025569 | 200.04174294328 | 0.0 | 78682.87850149203 | 78012.62794582798 | closed |
| ETH/USD | 15m | donchian_breakout | 2288.24 | 0.08741679 | 200.03059554959998 | 0.0 | 2311.5322058677275 | 2276.593897066136 | closed |
| AAVE/USD | 1h | trend_pullback | 135.566 | 1.475905837 | 200.08265069874201 | 0.0 | 139.92848587099192 | 133.38475706450404 | closed |
| BTC/USD | 5m | trend_pullback | 78478.03458866 | 0.002548899 | 200.03258388500086 | 0.0 | 78791.89551265999 | 78321.10412666 | closed |
| AAVE/USD | 5m | donchian_breakout | 128.26 | 1.560062402 | 200.09360368051998 | 0.0 | 129.28408688045377 | 127.7479565597731 | closed |
| ETH/USD | 15m | donchian_breakout | 2268.428166476 | 0.088233218 | 200.1507169300172 | 0.0 | 2287.218323230117 | 2259.0330880989413 | closed |
| TRUMP/USD | 5m | donchian_breakout | 1.601 | 124.937531234 | 200.02498750563402 | 0.0 | 1.6111050978694956 | 1.5959474510652523 | closed |
| BTC/USD | 5m | donchian_breakout | 77384.18 | 0.002586804 | 200.17770636071998 | 0.0 | 77693.44767373563 | 77229.54616313218 | closed |
| HYPE/USD | 5m | trend_pullback | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| UNI/USD | 1h | trend_pullback | 7.379 | 27.118644067 | 200.108474570393 | 0.0 | 7.736090787573656 | 7.200454606213172 | closed |
| ETH/USD | 1h | macd_momentum | 2301.9 | 0.086900074 | 200.0352803406 | 0.0 | 2357.8940243716884 | 2273.902987814156 | closed |
| LINK/USD | 15m | ema_cross | 11.13 | 17.977528089 | 200.08988763057002 | 0.0 | 11.341471359945134 | 11.024264320027434 | closed |
| HYPE/USD | 15m | donchian_breakout | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| POL/USD | 15m | donchian_breakout | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| SOL/USD | 15m | donchian_breakout | 93.8938 | 2.130814994 | 200.07031688363722 | 0.0 | 95.06239491305311 | 93.30950254347344 | closed |
| BTC/USD | 5m | bollinger_reversion | 78071.2 | 0.002561208 | 199.9565820096 | 0.0 | 78432.69577880135 | 77890.45211059932 | closed |
| BTC/USD | 5m | trend_pullback | 78544.311 | 0.002546619 | 200.022434734509 | 0.0 | 78942.66623833876 | 78345.13338083062 | closed |
| LINK/USD | 15m | donchian_breakout | 11.69 | 17.137960582 | 200.34275920358002 | 0.0 | 11.971892183110988 | 11.549053908444504 | closed |
| SOL/USD | 15m | donchian_breakout | 96.523 | 2.067758374 | 199.58624153360196 | 0.0 | 98.75804789759727 | 95.40547605120136 | closed |
| SOL/USD | 15m | trend_pullback | 95.17 | 2.102607232 | 200.10513026944 | 0.0 | 97.03783371062269 | 94.23608314468865 | closed |
| ONDO/USD | 15m | trend_pullback | 0.410972 | 486.570650058 | 199.96691319563638 | 0.0 | 0.42140262376781346 | 0.4057566881160933 | closed |
| LINK/USD | 15m | trend_pullback | 11.59 | 17.256255392 | 199.99999999328 | 0.0 | 11.807369977836238 | 11.48131501108188 | closed |
| RENDER/USD | 15m | trend_pullback | 1.62653 | 122.827488791 | 199.7825953432252 | 0.0 | 1.6700577053551326 | 1.6047661473224337 | closed |
| SOL/USD | 15m | donchian_breakout | 96.6316 | 2.068971224 | 199.92799972907844 | 0.0 | 97.98171627061451 | 95.95654186469275 | closed |

Order IDs, fill prices/times and quantities: orders.csv.
Closed trade cashflows: closed_trades.csv. Broker-reported fees: fees.csv.
Dust is kept in the ledger; it is not silently written off or counted as a win.

## Reconciliation

Status: matched
New entries blocked: False
Exit checks allowed: True
Accounting final: True

| Coin | Expected | Broker | Difference | Unconfirmed |
| --- | --- | --- | --- | --- |
| AAVEUSD | 0E-9 | 0 | 0E-9 | 0 |
| ARBUSD | 1217.948717948 | 1217.948717948 | 0E-9 | 0 |
| AVAXUSD | 0E-9 | 0 | 0E-9 | 0 |
| BTCUSD | 0.002476473 | 0.002476473 | 0E-9 | 0 |
| DOTUSD | 0E-9 | 0 | 0E-9 | 0 |
| ETHUSD | 0.077135081 | 0.077135081 | 0E-9 | 0 |
| FILUSD | 0E-9 | 0 | 0E-9 | 0 |
| HYPEUSD | 0 | 0 | 0 | 0 |
| LINKUSD | 17.361413279 | 17.361413279 | 0E-9 | 0 |
| ONDOUSD | 0E-9 | 0 | 0E-9 | 0 |
| PEPEUSD | 39820359.281437123 | 39820359.281437123 | 0E-9 | 0 |
| POLUSD | 0 | 0 | 0 | 0 |
| RENDERUSD | 124.117335987 | 124.117335987 | 0E-9 | 0 |
| SOLUSD | 0E-9 | 0 | 0E-9 | 0 |
| TRUMPUSD | 0E-9 | 0 | 0E-9 | 0 |
| UNIUSD | 0E-9 | 0 | 0E-9 | 0 |

Entry scan status: completed_with_data_errors
Next entry scan eligible: 2026-11-05T11:59:08+00:00
Entry scans: at most once every 30 minutes. Software exits: every successful workflow tick, not standing orders.
Full diagnostics: reconciliation.csv and reconciliation.json.

## Discovery watchlist

Last refresh: 2026-11-05T11:29:09+00:00
Source status: partial
Selected: ARB/USD, BTC/USD, ETH/USD, LINK/USD, PEPE/USD, RENDER/USD, AVAX/USD, LTC/USD, SOL/USD, ADA/USD, BCH/USD, TRUMP/USD
Emerging momentum is a screening label, not an undervaluation or profit claim.
News is attention/risk context, not a buy signal. Existing strategy, quote and risk checks still apply.
USD volume is estimated from Coinbase base volume times last price, not broker liquidity.
Details, exclusions, source errors and headline links: watchlist.json and watchlist.csv.
